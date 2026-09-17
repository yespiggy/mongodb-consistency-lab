#!/usr/bin/env python3
"""Build an evidence-linked report from one completed, audited measurement run."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape
from bson import json_util
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable

INK=colors.HexColor('#193349')
TEAL=colors.HexColor('#087F83')
GRAY=colors.HexColor('#526477')
PALE=colors.HexColor('#EDF5F7')
SOURCES=[
 ('MongoDB 7.0 Manual. Causal Consistency and Read and Write Concerns.',
  'https://www.mongodb.com/docs/v7.0/core/causal-consistency-read-write-concerns/'),
 ('MongoDB 7.0 Manual. Read Isolation, Consistency, and Recency.',
  'https://www.mongodb.com/docs/v7.0/core/read-isolation-consistency-recency/'),
 ('MongoDB 7.0 Manual. Write Concern.',
  'https://www.mongodb.com/docs/v7.0/reference/write-concern/'),
 ('MongoDB 7.0 Manual. Deploy a Self-Managed Replica Set for Testing and Development.',
  'https://www.mongodb.com/docs/v7.0/tutorial/deploy-replica-set-for-testing/'),
 ('MongoDB 7.0 Manual. Delayed Replica Set Members.',
  'https://www.mongodb.com/docs/v7.0/core/replica-set-delayed-member/'),
 ('PyMongo 4.10.1. client_session - Logical sessions for sequential operations.',
  'https://pymongo.readthedocs.io/en/4.10.1/api/pymongo/client_session.html'),
 ('MongoDB 7.0 Manual. Rollbacks During Replica Set Failover.',
  'https://www.mongodb.com/docs/v7.0/core/replica-set-rollbacks/'),
 ('MongoDB 7.0 Manual. Install MongoDB Community Edition.',
  'https://www.mongodb.com/docs/v7.0/administration/install-community/'),
 ('Docker. Install Docker Desktop on Mac.', 'https://docs.docker.com/desktop/setup/install/mac-install/'),
 ('Docker. Define services in Docker Compose.', 'https://docs.docker.com/reference/compose-file/services/'),
 ('Docker Hub. mongo - Docker Official Image.', 'https://hub.docker.com/_/mongo'),
]


class Architecture(Flowable):
    def __init__(self):
        super().__init__();self.width=480;self.height=133
    def draw(self):
        c=self.canv
        c.setFillColor(PALE);c.roundRect(100,98,280,30,5,fill=1,stroke=0)
        c.setFillColor(INK);c.setFont('Helvetica-Bold',10)
        c.drawCentredString(240,110,'Python client + experiment controller')
        for i,x in enumerate([4,165,326]):
            c.setStrokeColor(TEAL);c.line(240,98,x+75,69)
            c.setFillColor(PALE);c.roundRect(x,24,150,46,5,fill=1,stroke=0)
            c.setFillColor(INK);c.setFont('Helvetica-Bold',10)
            c.drawCentredString(x+75,53,f'mongo{i} | container')
            c.setFont('Helvetica',9)
            c.drawCentredString(x+75,37,'electable' if i<2 else 'secondary, priority 0')
            c.setFillColor(GRAY);c.setFont('Helvetica',8)
            c.drawCentredString(x+75,10,f'independent volume {i} / IP {i}')
        c.setStrokeColor(GRAY);c.setDash(3,2)
        c.line(80,24,80,0);c.line(80,0,402,0);c.line(240,24,240,0);c.line(402,24,402,0)
        c.setDash()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('results',type=Path)
    ap.add_argument('--out',type=Path,default=Path('report.pdf'))
    args=ap.parse_args()
    root=args.results
    meta=json.loads((root/'metadata.json').read_text())
    audit=json.loads((root/'audit.json').read_text())
    assert meta['deployment_type']=='docker-compose'
    assert meta['status']=='complete' and not audit['command_parameter_failures']
    assert not audit['isolation_failures']
    assert audit['trial_ids_unique']
    if 'db version v7.0.32' not in meta['mongod']:
        raise SystemExit('This report is scoped to MongoDB 7.0.32. Update the version-specific discussion and sources for another server version.')
    rows=json_util.loads((root/'trials.json').read_text())
    summary=json.loads((root/'summary.json').read_text())
    events=[json_util.loads(x) for x in (root/'history.jsonl').read_text().splitlines()]
    ss={(s['scenario'],s['config']):s for s in summary}
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleLab',fontName='Helvetica-Bold',fontSize=25,leading=29,textColor=INK,spaceAfter=12))
    styles.add(ParagraphStyle(name='SubLab',fontName='Helvetica',fontSize=11,leading=16,textColor=GRAY,spaceAfter=10))
    styles.add(ParagraphStyle(name='HeadLab',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=INK,spaceAfter=12))
    styles.add(ParagraphStyle(name='SmallHead',fontName='Helvetica-Bold',fontSize=11,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=6))
    styles.add(ParagraphStyle(name='BodyLab',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8,textColor=INK))
    styles.add(ParagraphStyle(name='CellLab',fontName='Helvetica',fontSize=8.2,leading=10.8,textColor=INK))
    styles.add(ParagraphStyle(name='TinyLab',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=6,textColor=GRAY))
    styles.add(ParagraphStyle(name='CodeLab',fontName='Courier',fontSize=8.1,leading=11,spaceAfter=7,textColor=INK))
    story=[]; md=[]
    def p(text,style='BodyLab'):
        story.append(Paragraph(text,styles[style]));md.append(text+'\n')
    def h(text): p(text,'SmallHead')
    def page(title):
        if story: story.append(PageBreak())
        p(title,'HeadLab');md.append('\n')
    def table(data,widths=None):
        content=[[Paragraph(escape(str(cell)),styles['CellLab']) for cell in row] for row in data]
        t=Table(content,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('LINEBELOW',(0,0),(-1,0),1,TEAL),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D7E2E7')),
                              ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                              ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.append(t);story.append(Spacer(1,8))
        md.extend([' | '.join(map(str,r)) for r in data]);md.append('\n')
    names={'normal':'Normal','replication_lag':'3 s replica lag','secondary_crash':'Secondary crash',
           'primary_crash':'Primary crash','network_partition':'1+1+1 partition','partition_rollback':'Partition + rollback'}
    def result_table(scenarios):
        data=[['Scenario / config','n','RYW','MR','MW','WFR','Errors / ops']]
        for scenario in scenarios:
            for cfg in 'ABCD':
                s=ss[(scenario,cfg)]
                cells=[f"{s['checks'][m]['violations']}/{s['checks'][m]['eligible']}" if s['checks'][m]['eligible'] else '--'
                       for m in ['RYW','MR','MW','WFR']]
                data.append([f'{names[scenario]} / {cfg}',s['histories'],*cells,f"{s['errors']}/{s['operations']}"])
        table(data,[160,25,49,49,49,49,78])

    p('Client-centric consistency<br/>in a replicated MongoDB database','TitleLab')
    p('Experimental report | three Docker containers | MongoDB 7.0.32','SubLab')
    p('Group members / student IDs: __________________________________________','TinyLab')
    p('Prepared from a completed local run. Group identity and course-specific formatting require author review before submission.','TinyLab')
    h('Research question')
    p('How do read concern, write concern, and causal history tracking affect read-your-writes, monotonic reads, monotonic writes, and writes-follow-reads when replicas lag, fail, or cannot communicate?')
    p(f'The experiment contains <b>{len(rows)} measured histories</b> across four configurations and six scenarios. '
      'It runs real MongoDB processes and records returned values, errors, causal tokens, fault events, and the actual commands sent by the driver. '
      'Synthetic checker examples and debugging runs are excluded.')
    h('Main result')
    a=ss[('replication_lag','A')]['checks']['RYW'];b=ss[('replication_lag','B')]['checks']['RYW']
    p(f'With a delayed secondary, A returned stale data in {a["violations"]}/{a["eligible"]} eligible read-your-writes checks and B did so in '
      f'{b["violations"]}/{b["eligible"]}. B uses majority reads and writes but does not propagate causal read bounds. '
      'Causal configurations instead waited for their required history, sometimes reaching the read deadline. '
      'This distinguishes consistency of successful observations from operation availability.')
    h('Deployment')
    story.append(Architecture());story.append(Spacer(1,13))
    p('Three Linux containers run under Docker Desktop on one Mac. Each has its own IP address, process, and named data volume. '
      'The solid paths are client connections through loopback-published ports; the dashed path is the Docker bridge network used for replication and heartbeats. '
      'This matches the assignment option of multiple Docker containers on one machine. [4, 10, 11]')
    p(f'Measurement start: {escape(meta["started_utc"])}<br/>Evidence directory: {escape(root.name)}','TinyLab')

    page('1. Configuration choices and predictions')
    p('MongoDB read concern controls the visibility conditions of returned data; write concern controls the acknowledgment conditions of writes. '
      'A majority write needs the voting majority, here two data-bearing members. A majority read can still be older than this client\'s latest write. '
      'Write concern timeouts do not establish that a write had no effect. [2, 3]')
    table([['ID','Causal tracking','Read concern','Write concern'],
           ['A','off','local','w:1'],['B','off','majority','w:majority'],
           ['C','on','majority','w:1'],['D','on','majority','w:majority']],[35,130,145,149])
    p('Causal tracking uses sequential explicit sessions. When the application changes direct connections, it passes both cluster time and operation time to a session owned by the next MongoClient. '
      'A causal read includes an afterClusterTime bound. A/B still use explicit sessions, with causal_consistency=False. [6]')
    h('Predictions made before the completed measurement run')
    table([['Configuration','RYW','MR','MW','WFR'],
           ['A: local / 1, causal off','NG','NG','NG*','NG'],
           ['B: majority / majority, causal off','NG','NG','E*','E*'],
           ['C: majority / 1, causal on','NG*','G','NG*','G'],
           ['D: majority / majority, causal on','G','G','G','G']],[239,55,55,55,55])
    p('<b>G</b> = documented guarantee under the stated causal settings; <b>NG</b> = not guaranteed for every permitted history; '
      '<b>E</b> = expected in this single-replica-set experiment from the committed-prefix argument, not a general cross-deployment guarantee. '
      'An NG entry does not predict that every trial will violate the property. [1]')
    p('<b>* Durability matters.</b> This report requires an acknowledged predecessor to remain represented across failover. '
      'Under this interpretation C can lose RYW and MW when a w:1 write rolls back. MongoDB also describes a weaker interpretation that permits rollback as part of the history. '
      'Those interpretations should not be mixed. [1, 7]')
    p('For B, acknowledged majority writes and successful majority reads belong to the durable replicated history. '
      'We therefore expect a later successfully acknowledged majority write on this replica set to incorporate those predecessors. '
      'This is our topology-specific inference. The same claim is not asserted for sharded or unrelated deployments.')
    p('MongoDB also documents default monotonic write ordering for ordinary modifying writes on a replica set. '
      'We distinguish that execution-order statement from retaining a w:1 predecessor after rollback; W1 and W2 here are real modifying writes. [2]')

    page('2. Workload, observations, and checker')
    p('Every trial has a unique document initialized to <font face="Courier">{a:0, b:0}</font>. '
      'Initialization is acknowledged by all three members and checked in their majority snapshots before faults. '
      'No competing client overwrites the trial document, so a=0 and a=1 have an unambiguous version order.')
    table([['Operation','Meaning'],['W1','Set a=1; record acknowledgment or error.'],
           ['R1','Read the current primary; record a and the session tokens.'],
           ['R2','Read a known secondary, or the new primary after failover.'],
           ['W2','Set b=1 using findOneAndUpdate; atomically return the pre-image.']], [70,389])
    p('The usual sequence is W1, R1, R2, W2. In the rollback scenario the order is W1, R1, failover, W2, R2. '
      'Returning W2\'s pre-image reveals the state at execution of the dependent write. A final read alone would not establish this ordering.')
    table([['Property','Eligible check','Violation witness'],
           ['Read-your-writes (RYW)','W1 acknowledged; R2 returns','R2.a < 1'],
           ['Monotonic reads (MR)','R1 and R2 both return','R2.a < R1.a'],
           ['Monotonic writes (MW)','W1 and W2 acknowledged','W2 pre-image a < 1'],
           ['Writes-follow-reads (WFR)','W2 acknowledged; an earlier read returned','W2 pre-image a < maximum a observed by reads completed before W2']], [100,159,200])
    p('These checks operationalize the four session properties on a deliberately small, append-only version progression. [2] '
      'They are overlapping checks of one workload, not independent general-purpose verification algorithms. '
      'The checker uses actual invocation/completion order when selecting the reads that precede W2.')
    h('Errors and eligibility')
    p('Read errors expose no version. Write errors can have an unknown outcome and are not counted as acknowledged predecessors. '
      'When a prerequisite is missing, its property check is inconclusive. Successful stale reads are violations; waiting, timeouts, and unavailable nodes are reported separately. '
      'Thus 0/0 is not described as a consistency success. [3]')
    h('Instrumentation and validation')
    p(f'The completed run records {audit["operations"]} attempted operations and {audit["wire_commands"]} corresponding application commands. '
      'The audit checks actual read/write concerns and the presence or absence of causal read bounds. '
      'Seven synthetic checker tests cover stale reads, unknown writes, timeouts, rollback, and WFR operation order. '
      'These validate classification logic; they are not experimental observations.')

    page('3. Scenarios and experimental controls')
    table([['Scenario','Fault / routing','Histories per configuration'],
           ['Normal','No injected fault; R2 targets node 2.',meta['arguments']['normal']],
           ['Replica lag','Node 2 applies operations with a 3 s delay; R2 targets it.',meta['arguments']['lag']],
           ['Secondary crash','SIGKILL node 2; R2 targets the surviving secondary.',meta['arguments']['failure']],
           ['Primary crash','W1, R1; SIGKILL primary; await election; R2, W2 on new primary.',meta['arguments']['fault_repeats']],
           ['Network partition','Drop inter-container packets while all servers stay alive; test transient and sustained loss of quorum.',meta['arguments']['fault_repeats']],
           ['Partition + rollback','Partition before W1; R1; kill old primary; heal survivors; new primary executes W2, R2.',meta['arguments']['fault_repeats']]], [95,299,65])
    p('The partition is explicitly <b>1+1+1</b>: every member is isolated from every other member. '
      'Host-client connections remain available. Container-local iptables INPUT/OUTPUT rules drop packets from/to peer container IPs, affecting both replication and heartbeat traffic. '
      'This is different from pausing a database process, and different from a 2+1 split with an available majority side.')
    p('Each network trial has its own cut/heal cycle. The old primary may accept w:1 writes briefly before detecting quorum loss. '
      'The network-only scenario then waits for step-down and attempts an additional write, W_unavailable. '
      'The rollback scenario kills the old primary before reconnecting survivors, so its isolated W1 cannot become part of their elected history.')
    p('After each disruptive trial, restart any stopped container, remove the packet-drop rules, and wait for an administrative w:3 recovery barrier. '
      'Inspect all replicas after healing. Recovery uses longer administrative deadlines than measured application operations. '
      'The healthy primary-crash experiment deliberately has no extra durability barrier between W1 and the crash.')
    h('Deliberate lag control')
    p('Node 2 is priority 0 and receives secondaryDelaySecs=3 only during lag tests, then returns to 0. '
      'It remains visible and voting for this controlled experiment. MongoDB recommends hidden, non-voting delayed members for production; '
      'our deviation permits direct session-based stale-read tests while keeping a fixed three-voter topology. '
      'The two fast members can still acknowledge majority writes. [5]')
    h('Timing and repeatability')
    p('Configuration order is shuffled within each scenario with seed 419. Scenario order remains fixed. '
      'The read server deadline is 700 ms, write concern timeout 900 ms, driver socket timeout 2500 ms, and server-selection timeout 1600 ms. '
      'W2 has a separate 1800 ms server limit. Driver retries are disabled. '
      'Elections use a 15 s configured timeout and 0.5 s heartbeats. These choices prioritize short, observable failure windows over throughput measurement.')

    page('4. Results: normal, lag, and secondary failure')
    p('Each property cell is <b>violations / eligible checks</b>. "--" means no eligible check. '
      'The final column counts operation errors over attempts, not failed property checks. '
      'An operation can participate in several properties, so the property columns must not be summed as independent trials.','TinyLab')
    result_table(['normal','replication_lag','secondary_crash'])
    h('What these observations show')
    p('The delayed-replica test separates majority visibility from client history. '
      'A/B can read an older version that is already committed at the replica, even after the same logical application has written or read a newer version. '
      'C/D send a causal lower bound: their delayed-replica reads cannot return the older version merely to meet the deadline.')
    p('A causal read that times out contributes an inconclusive RYW/MR check and an operation error. '
      'It is evidence of waiting or unavailability under this deadline, not proof that the property holds in all executions. '
      'W2 can still succeed on the up-to-date primary and provide an eligible MW/WFR check.')
    p('The secondary-crash scenario leaves two voting, data-bearing members. It therefore differs from a complete partition: '
      'the surviving pair can replicate and acknowledge majority operations. Any absence of observed violations applies only to the sampled histories.')

    page('5. Results: failover and network partitions')
    p('Cells use the same violations / eligible convention. Network-only histories contain five attempted operations because they include the additional sustained-quorum-loss write probe.','TinyLab')
    result_table(['primary_crash','network_partition','partition_rollback'])
    probe=[r['operations']['W_unavailable'] for r in rows if r['scenario']=='network_partition']
    h('Availability under sustained isolation')
    p(f'After the old primary stepped down, {sum(o["status"]=="error" for o in probe)}/{len(probe)} additional write probes returned errors. '
      f'All {audit["isolation_snapshots"]} isolated topology snapshots showed no primary and zero health for remote peers as viewed by every member. '
      'The servers remained directly reachable by the controller, distinguishing these live-but-isolated processes from the separate SIGKILL tests.')
    h('Rollback changes the meaning of acknowledgment')
    p('An isolated w:1 write can be acknowledged on the old primary and still be absent on the newly elected history. '
      'When a later acknowledged write executes on state a=0, it witnesses loss of the acknowledged predecessor under our durable-history MW definition. '
      'If the client previously read a=1, the same pre-image can also witness a WFR violation. Majority write attempts during complete isolation cannot obtain a majority acknowledgment. [7]')
    p('No eligible check is created by treating an errored majority write as acknowledged. '
      'Similarly, a majority causal read that cannot obtain its required history supplies no observed version for MR or WFR. '
      'This explains why some strong-setting entries are inconclusive rather than reported as passes.')

    page('6. Inspectable histories and latency')
    candidates=[('A stale secondary read','replication_lag','A','RYW'),
                ('Majority without causal tracking','replication_lag','B','MR'),
                ('A rollback ordering violation','partition_rollback','A','WFR'),
                ('Causal w:1 and durable history','partition_rollback','C','MW')]
    for title,scenario,cfg,model in candidates:
        matches=[r for r in rows if r['scenario']==scenario and r['config']==cfg and r['checks'][model] is True]
        h(title)
        if not matches:
            p(f'No eligible violating {model} history was observed for this case.','TinyLab');continue
        r=matches[0]
        bits=[]
        for op in sorted(r['operations'].values(),key=lambda o:o['invocation_ns']):
            if op['status']=='ok':
                val=op['value'];value=f'a={val["a"]}' if 'a' in val else 'ack'
            else:value=f'error {op.get("error_code")}'
            bits.append(f'{op["label"]}@n{op["node"]}: {value}')
        p(escape(r['trial'])+'<br/>'+escape(' -> '.join(bits)),'CodeLab')
        p(f'Checker result: {model} violation. Locate this trial ID in history.jsonl to inspect exact timestamps, concerns, tokens, and error details.','TinyLab')
    h('Read latency in normal operation')
    data=[['Config','Successful R2 / attempted R2','Median successful R2 (ms)']]
    for cfg in 'ABCD':
        s=ss[('normal',cfg)]
        data.append([cfg,f'{s["r2_successes"]}/{s["histories"]}',f'{s["r2_median_ms"]:.2f}' if s['r2_median_ms'] is not None else '--'])
    table(data,[55,220,184])
    p('These are client-observed timings for a small Docker-on-one-host workload. Only successful reads enter the median; deadlines and errors are reported separately. '
      'Small timing differences are not a reliable performance ranking. Fixed scenario order, scheduler effects, and limited fault repetitions prevent strong statistical claims.')

    page('7. Interpretation and limitations')
    h('Comparison with the predictions')
    p('The stale-read witnesses under A/B agree with the prediction that read routing plus read/write concerns alone need not preserve the client\'s observed history. '
      'Majority describes commitment, while the causal bound describes how far this particular session must have advanced. '
      'The rollback experiment separately tests whether an acknowledged write remains part of the history after a primary change.')
    total_d={m:sum(r['checks'][m] is True for r in rows if r['config']=='D') for m in ['RYW','MR','MW','WFR']}
    p(f'Configuration D produced {sum(total_d.values())} witnessed property violations in this run. '
      'Its successful observations and deadline failures must be read together: refusing or delaying an operation is compatible with protecting a consistency guarantee. '
      'Finite successful tests cannot establish a universal guarantee; the documented guarantee and these observations are different kinds of evidence.')
    h('Limits of this experiment')
    limits=[
      'All containers share one physical Mac and the Docker Linux VM. Separate network/process namespaces and volumes provide distinct logical nodes, but do not provide independent hardware, kernel, disk, or power failure domains.',
      'Docker Desktop forwards the client ports into its Linux VM. These timings include virtualization and port-forwarding overhead and should not be generalized to a multi-machine or cloud deployment.',
      'The network test is 1+1+1. It does not measure availability on the majority side of a 2+1 split, asymmetric partitions, gradual packet loss, or geographic latency.',
      'A visible, voting delayed secondary is a deliberate laboratory control, not MongoDB\'s recommended production design. Three seconds of configured delay is not a measured WAN delay.',
      'Reads are deliberately routed to specific members with direct connections. The harness tests explicit causal metadata propagation across physical sessions; it does not characterize default driver load balancing or session misuse by arbitrary applications.',
      'One document, one monotone version field, and sequential operations simplify the oracle. This does not test cross-document causality, transactions, sharding, concurrent overwrites, general linearizability, or all possible executions.',
      'The four property checks overlap. Small fault sample sizes and deterministic orchestration provide counterexamples and illustrations, not independent estimates of production anomaly rates.',
      'Reported MW/RYW rollback violations use the durable-history interpretation. MongoDB\'s rollback-permitting terminology can classify such histories differently; the definition is explicit in Section 1.',
    ]
    for i,text in enumerate(limits,1):p(f'<b>{i}.</b> {text}')

    page('8. Installation, reproduction, and provenance')
    p('Docker Desktop 4.91.0 was installed from the official Apple-silicon download. In this restricted environment, its disk image was extracted without mounting; '
      'the resulting Docker.app passed Apple codesign deep/strict verification before being installed in /Applications and launched. '
      'The normal reproduction route is the official Docker Desktop installer. Compose builds from mongo:7.0.32 and adds iptables for fault injection. [10, 12]')
    table([['Component','Recorded value'],['Server','MongoDB Community 7.0.32; arm64'],
           ['Host OS',meta['platform']],
           ['Docker Desktop / Engine','4.91.0 / '+json.loads(meta['deployment']['docker_version'])['Server']['Version']],
           ['Compose',meta['deployment']['compose_version']],['Python / driver',f'{meta["python"]} / PyMongo {meta["pymongo"]}'],
           ['Replica set','cc_lab; 3 voters, 3 data copies, no arbiter'],
           ['Storage per process','128 MB oplog; WiredTiger cache 0.25 GB'],
           ['Network',f'Host ports {meta["arguments"]["base_port"]}-{meta["arguments"]["base_port"]+2}; mongo0/1/2:27017 on bridge'],
           ['Isolation','New Compose project and three named volumes per run; NET_ADMIN for fault rules']], [130,329])
    p('Start Docker Desktop, then run the commands below from the kit directory. The runner builds the image, creates three containers, '
      'initializes cc_lab with mongo0/1/2:27017, and waits for one primary and two secondaries. Nodes 0/1 have priority 1; node 2 has priority 0; all have one vote. '
      'Each container runs mongod --replSet cc_lab --bind_ip_all with the storage limits above. [4, 11]')
    for cmd in ['python3 -m venv .venv','.venv/bin/python -m pip install -r requirements.txt',
                '.venv/bin/python -m unittest -v test_checker.py',
                '.venv/bin/python run.py --work-dir work/repeat-data<br/>  --out results/repeat',
                '.venv/bin/python analyze.py results/repeat',
                '.venv/bin/python make_report.py results/repeat<br/>  --out repeat-report.pdf']:
        p(cmd,'CodeLab')
    p('Wrapped commands are single shell commands. Each run creates fresh volumes and refuses existing result directories. '
      'The script stops its containers after collecting results; data volumes are retained. Metadata includes image IDs, container/network/volume details and versions. '
      'The README documents inspection and explicit cleanup. No earlier native-process measurements are reused.')
    h('AI usage and group review')
    p('[9] OpenAI Codex, project assistance interactions, 14 and 17 September 2026. The user supplied the assignment. '
      'The assistant helped select the database, interpret documentation, design experiments, write and debug code, execute local database tests, analyze logs, and draft this report. '
      'Database measurements were generated by real MongoDB executions. This interaction is the source of the AI assistance, not an external database guarantee.')

    page('9. References and evidence manifest')
    p('Documentation consulted on 14 and 17 September 2026. Version-specific pages are used where available. '
      'Numbered citations identify the relevant source; the source code and raw run files provide the experiment\'s own evidence.','TinyLab')
    for i,(title,url) in enumerate(SOURCES,1):
        if i>=9: i+=1  # [9] is the private AI interaction.
        p(f'<b>[{i}]</b> {escape(title)}<br/><link href="{escape(url)}" color="#087F83">{escape(url)}</link>','TinyLab')
    p('<b>[9]</b> OpenAI Codex. Project assistance interaction with the group requester, 2026-09-14 and 2026-09-17. '
      'Assignment prompt, design discussion, implementation, execution, analysis, and report drafting. Private interaction; retain/export it if the course requires an AI transcript.','TinyLab')
    h('Completed run identity')
    p(f'Started: {escape(meta["started_utc"])}<br/>Finished: {escape(meta["finished_utc"])}<br/>'
      f'Run status: {meta["status"]}; histories: {len(rows)}; application commands: {audit["wire_commands"]}; parameter-audit failures: 0.','TinyLab')
    p('Harness SHA-256 recorded at execution:<br/>'+escape(meta.get('harness_sha256','not recorded')),'TinyLab')
    for name in ['history.jsonl','trials.json','metadata.json']:
        digest=hashlib.sha256((root/name).read_bytes()).hexdigest()
        p(escape(name)+' SHA-256:<br/>'+digest,'TinyLab')
    p('The kit includes the exact harness, checker tests, analysis script, report builder, dependency pins, a reproduction guide, and the identified completed run. '
      'Review the JSON histories by trial ID rather than inferring guarantees from screenshots or a final document value.','TinyLab')

    args.out.parent.mkdir(parents=True,exist_ok=True)
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#D7E2E7'));canvas.line(19*mm,17*mm,191*mm,17*mm)
        canvas.setFont('Helvetica',8);canvas.setFillColor(GRAY)
        canvas.drawString(19*mm,12*mm,'MongoDB consistency experiment | measured Docker run')
        canvas.drawRightString(191*mm,12*mm,str(doc.page))
    doc=SimpleDocTemplate(str(args.out),pagesize=(210*mm,297*mm),rightMargin=19*mm,leftMargin=19*mm,
                          topMargin=18*mm,bottomMargin=23*mm,title='Client-centric consistency in MongoDB',author='Group identity pending')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    args.out.with_suffix('.md').write_text('\n'.join(md))
    print(args.out.resolve())


if __name__=='__main__':main()
