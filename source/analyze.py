#!/usr/bin/env python3
"""Summarize measured histories and audit the actual driver commands."""
import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from bson import json_util


def analyze(root):
    metadata=json.loads((root/'metadata.json').read_text())
    configs=metadata['configs']
    rows=json_util.loads((root/'trials.json').read_text())
    groups=defaultdict(list)
    for row in rows: groups[(row['scenario'],row['config'])].append(row)
    summary=[]
    for (scenario,config), values in groups.items():
        ops=[o for row in values for o in row['operations'].values()]
        checks={model:dict(eligible=sum(r['checks'][model] is not None for r in values),
                          violations=sum(r['checks'][model] is True for r in values),
                          inconclusive=sum(r['checks'][model] is None for r in values))
                for model in ['RYW','MR','MW','WFR']}
        latencies=sorted(o['latency_ms'] for o in ops if o['status']=='ok')
        r2=sorted(row['operations']['R2']['latency_ms'] for row in values
                  if row['operations']['R2']['status']=='ok')
        summary.append(dict(scenario=scenario,config=config,histories=len(values),checks=checks,
                       operations=len(ops),errors=sum(o['status']=='error' for o in ops),
                       successful_operation_p50_ms=statistics.median(latencies) if latencies else None,
                       successful_operation_p95_ms=latencies[math.ceil(len(latencies)*.95)-1] if latencies else None,
                       r2_successes=len(r2),r2_median_ms=statistics.median(r2) if r2 else None))
    events=[json_util.loads(line) for line in (root/'history.jsonl').read_text().splitlines()]
    wire=[e for e in events if e['kind']=='wire_command']
    by_trial={r['trial']:r for r in rows}
    failures=[]
    wire_keys=[]
    for e in wire:
        cmd=e['command']
        _,key,label=cmd['comment'].split(':')
        wire_keys.append((key,label))
        cfg=by_trial[key]['config']
        if cfg not in configs:
            failures.append([key,label,'configuration missing from metadata',cfg])
            continue
        rc=configs[cfg]['read']
        wc=configs[cfg]['write']
        causal=configs[cfg]['causal']
        if label.startswith('W') and cmd.get('writeConcern',{}).get('w')!=wc:
            failures.append([key,label,'wrong write concern'])
        if label.startswith('R'):
            read=cmd.get('readConcern',{})
            if read.get('level')!=rc: failures.append([key,label,'wrong read concern'])
            if causal and by_trial[key]['operations'][label]['input_operation_time'] is not None:
                if 'afterClusterTime' not in read: failures.append([key,label,'missing causal bound'])
            if not causal and 'afterClusterTime' in read:
                failures.append([key,label,'unexpected causal bound'])
    measured_ops=sum(len(row['operations']) for row in rows)
    wire_key_set=set(wire_keys)
    duplicate_wire_commands=len(wire_keys)-len(wire_key_set)
    precommand_errors=[]
    wire_coverage_failures=[]
    for row in rows:
        for label,op in row['operations'].items():
            key=(row['trial'],label)
            if key in wire_key_set:
                continue
            # PyMongo can reject an operation before sending a command, for example
            # while a restarted direct connection temporarily has no replica-set
            # session capability. Such attempts are real availability errors but
            # cannot have a command-monitoring event.
            if op['status']=='error' and op.get('error_type') in {
                    'ConfigurationError','ServerSelectionTimeoutError','AutoReconnect'}:
                precommand_errors.append(dict(trial=row['trial'],label=label,
                                              error_type=op.get('error_type')))
            else:
                wire_coverage_failures.append([row['trial'],label,op['status'],
                                               op.get('error_type')])
    if duplicate_wire_commands:
        wire_coverage_failures.append(['global','duplicate-wire-commands',
                                       duplicate_wire_commands])
    isolation=[e for e in events if e['kind']=='topology' and e['label'].endswith('-isolated')]
    isolation_failures=[]
    for e in isolation:
        for node,status in e['nodes'].items():
            if not isinstance(status,dict):
                isolation_failures.append([e['label'],node,'no status']);continue
            scenario=by_trial[e['label'].removesuffix('-isolated')]['scenario']
            if scenario=='network_partition' and status['myState']==1:
                isolation_failures.append([e['label'],node,'still primary'])
            for member in status['members']:
                if member.get('self'):
                    continue
                peer=int(member['name'].split('mongo',1)[1].split(':',1)[0])
                minority=by_trial[e['label'].removesuffix('-isolated')]['operations']['R2']['node']
                should_reach = scenario=='network_partition_2_1' and int(node) != minority and peer != minority
                if scenario=='network_partition' and member['health']!=0:
                    isolation_failures.append([e['label'],node,member['name'],'still reachable'])
                if scenario=='network_partition_2_1' and should_reach != (member['health']==1):
                    isolation_failures.append([e['label'],node,member['name'],'unexpected 2+1 reachability'])
    expected_isolation=sum(r['scenario'] in ('network_partition','network_partition_2_1') for r in rows)
    if len(isolation)!=expected_isolation:
        isolation_failures.append(['missing snapshots',len(isolation),expected_isolation])
    audit=dict(histories=len(rows),operations=measured_ops,wire_commands=len(wire),
               precommand_errors=precommand_errors,
               wire_coverage_failures=wire_coverage_failures,
               command_parameter_failures=failures,
               isolation_snapshots=len(isolation),isolation_failures=isolation_failures,
               trial_ids_unique=len(by_trial)==len(rows),
               run_status=metadata['status'])
    (root/'summary.json').write_text(json.dumps(summary,indent=2))
    (root/'audit.json').write_text(json.dumps(audit,indent=2))
    lines=['# Measured results','',
           'Cells show violations / eligible checks; a dash means no eligible check. Timeouts are not violations.','',
           '| Scenario | Config | Histories | RYW | MR | MW | WFR | Operation errors |',
           '|---|---|---:|---:|---:|---:|---:|---:|']
    for s in summary:
        cells=[f"{c['violations']}/{c['eligible']}" if c['eligible'] else '-' for c in s['checks'].values()]
        lines.append('| '+' | '.join([s['scenario'],s['config'],str(s['histories']),*cells,
                                     f"{s['errors']}/{s['operations']}"])+' |')
    (root/'summary.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
    print(json.dumps(audit,indent=2))
    if failures or wire_coverage_failures or isolation_failures or not audit['trial_ids_unique'] or audit['run_status']!='complete':
        raise SystemExit('Audit failed; inspect results before using them in a report')
    return summary,audit


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('results',type=Path)
    analyze(p.parse_args().results)
