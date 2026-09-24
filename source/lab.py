#!/usr/bin/env python3
"""Isolated, real MongoDB replica-set experiments. No existing databases are used."""
import argparse
import hashlib
import json
import platform
import random
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pymongo
from bson import json_util
from pymongo import MongoClient, ReadPreference, ReturnDocument, monitoring
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

CONFIGS = {
    # Matched causal-session pairs. Within each adjacent pair, read concern and
    # write concern are identical; only causal history tracking changes.
    'A': dict(causal=False, read='local', write=1),
    'B': dict(causal=True, read='local', write=1),
    'C': dict(causal=False, read='local', write='majority'),
    'D': dict(causal=True, read='local', write='majority'),
    'E': dict(causal=False, read='majority', write=1),
    'F': dict(causal=True, read='majority', write=1),
    'G': dict(causal=False, read='majority', write='majority'),
    'H': dict(causal=True, read='majority', write='majority'),
}
MAX_READ_MS = 5000
SOCKET_TIMEOUT_MS = 7000
WRITE_TIMEOUT_MS = 5000


class Log:
    def __init__(self, path):
        self.f = path.open('w')
        self.lock = threading.Lock()

    def emit(self, kind, **data):
        with self.lock:
            self.f.write(json_util.dumps(dict(kind=kind, utc=datetime.now(timezone.utc),
                                             monotonic_ns=time.monotonic_ns(), **data)) + '\n')
            self.f.flush()


class Commands(monitoring.CommandListener):
    def __init__(self, log):
        self.log = log

    def started(self, event):
        if event.command.get('comment', '').startswith('trial:'):
            self.log.emit('wire_command', request_id=event.request_id,
                          server=event.connection_id, command=dict(event.command))

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass




class Cluster:
    def __init__(self, work, log, base=29101):
        self.work, self.log = work, log
        self.back = [base+i for i in range(3)]
        self.procs = [None]*3
        self.clients = []
        self.mesh = None


    def make_clients(self):
        self.clients = [MongoClient('127.0.0.1', port, directConnection=True,
                       retryReads=False, retryWrites=False,
                       serverSelectionTimeoutMS=1600, connectTimeoutMS=800,
                       socketTimeoutMS=SOCKET_TIMEOUT_MS, heartbeatFrequencyMS=500,
                       event_listeners=[Commands(self.log)]) for port in self.back]



    def hello(self, i):
        return self.clients[i].admin.command('hello')

    def primary(self, exclude=None):
        def find():
            for i in range(3):
                if i == exclude or not self.procs[i] or self.procs[i].poll() is not None:
                    continue
                try:
                    if self.hello(i).get('isWritablePrimary'):
                        return (i,)
                except pymongo.errors.PyMongoError:
                    pass
            return False
        return wait_for(find, 40)[0]

    def seed(self, ids):
        c = self.clients[self.primary()].lab.records.with_options(write_concern=WriteConcern(w=3, wtimeout=20000))
        c.insert_many([dict(_id=k, a=0, b=0) for k in ids])
        # Acknowledgment and visibility of each member's committed snapshot are
        # distinct. Establish the initial version on every read target before faults.
        for client in self.clients:
            col=client.lab.records.with_options(read_concern=ReadConcern('majority'),
                  read_preference=ReadPreference.SECONDARY_PREFERRED)
            wait_for(lambda col=col: col.count_documents({'_id':{'$in':ids}},maxTimeMS=1000)==len(ids),20)
        self.log.emit('seed', count=len(ids), write_concern=3)

    def barrier(self, key):
        # Recovery is an administrative phase, with a longer timeout than measured
        # operations. A restarted node may need more than the 2.5 s client deadline.
        def synced():
            with MongoClient('127.0.0.1',self.back[self.primary()],directConnection=True,
                             socketTimeoutMS=25000,serverSelectionTimeoutMS=1500,
                             retryWrites=False) as admin:
                admin.lab.barriers.with_options(write_concern=WriteConcern(w=3,wtimeout=20000)).replace_one(
                    {'_id':key},{'_id':key,'generation':time.time_ns()},upsert=True)
                return True
        wait_for(synced,60)

    def delay(self, seconds):
        c = self.clients[self.primary()]
        cfg = c.admin.command('replSetGetConfig')['config']
        cfg['version'] += 1
        cfg['members'][2]['secondaryDelaySecs'] = seconds
        c.admin.command('replSetReconfig', cfg)
        wait_for(lambda: self.clients[2].admin.command('replSetGetConfig')['config']['version'] >= cfg['version'], 15)
        self.log.emit('replication_delay', node=2, seconds=seconds)

    def snapshot(self, label):
        result = {}
        for i in range(3):
            try:
                result[str(i)] = self.clients[i].admin.command('replSetGetStatus')
            except pymongo.errors.PyMongoError as e:
                result[str(i)] = str(e)
        self.log.emit('topology', label=label, nodes=result)



def wait_for(fn, seconds):
    end = time.monotonic()+seconds
    last = None
    while time.monotonic() < end:
        try:
            value = fn()
            if value:
                return value
        except pymongo.errors.PyMongoError as e:
            last = e
        time.sleep(.15)
    raise TimeoutError(f'Condition not met after {seconds}s; last error: {last}')


class Trial:
    """One logical application history; physical sessions are owned per MongoClient.

    Causal metadata is explicitly propagated when changing the target connection.
    No ClientSession is ever passed to a MongoClient that did not create it.
    """
    def __init__(self, cluster, key, scenario, config):
        self.cluster, self.key, self.scenario, self.config = cluster, key, scenario, config
        self.cfg = CONFIGS[config]
        self.sessions = [c.start_session(causal_consistency=self.cfg['causal']) for c in cluster.clients]
        self.cluster_time = self.operation_time = None
        self.ops = {}

    def op(self, label, node):
        c, s = self.cluster.clients[node], self.sessions[node]
        if self.cfg['causal']:
            if self.cluster_time:
                s.advance_cluster_time(self.cluster_time)
            if self.operation_time:
                s.advance_operation_time(self.operation_time)
        col = c.lab.records.with_options(read_concern=ReadConcern(self.cfg['read']),
              write_concern=WriteConcern(w=self.cfg['write'], wtimeout=WRITE_TIMEOUT_MS),
              read_preference=ReadPreference.SECONDARY_PREFERRED)
        began = time.monotonic_ns()
        result = dict(label=label, node=node, invocation_ns=began,
                      input_operation_time=self.operation_time)
        try:
            comment = f'trial:{self.key}:{label}'
            if label == 'W_unavailable':
                r = col.update_one({'_id':self.key}, {'$set':{'unavailable_probe':True}}, session=s, comment=comment)
                value = {'matched':r.matched_count, 'modified':r.modified_count}
            elif label == 'W1':
                r = col.update_one({'_id':self.key}, {'$set':{'a':1}}, session=s, comment=comment)
                if r.matched_count != 1 or r.modified_count != 1:
                    raise RuntimeError('W1 did not modify exactly one existing document')
                value = {'matched': r.matched_count, 'modified': r.modified_count}
            elif label == 'W2':
                # Atomic pre-image records the state at execution of a real modifying write.
                value = col.find_one_and_update({'_id':self.key}, {'$set':{'b':1}},
                         return_document=ReturnDocument.BEFORE, session=s,
                         maxTimeMS=1800, comment=comment)
                if value is None:
                    raise RuntimeError('Missing seeded document at W2')
            else:
                value = col.find_one({'_id':self.key}, session=s, max_time_ms=MAX_READ_MS, comment=comment)
                if value is None:
                    raise RuntimeError('Missing seeded document at read')
            result.update(status='ok', value=value)
        except pymongo.errors.PyMongoError as e:
            result.update(status='error', error_type=type(e).__name__, error_code=getattr(e,'code',None),
                          error=str(e), details=getattr(e,'details',None),
                          outcome='unknown' if label.startswith('W') else 'no_value')
        finally:
            if s.cluster_time and (not self.cluster_time or s.cluster_time['clusterTime'] > self.cluster_time['clusterTime']):
                self.cluster_time = s.cluster_time
            if s.operation_time and (not self.operation_time or s.operation_time > self.operation_time):
                self.operation_time = s.operation_time
            result.update(completion_ns=time.monotonic_ns(), operation_time=s.operation_time)
            result['latency_ms'] = (result['completion_ns']-began)/1e6
        self.ops[label] = result
        self.cluster.log.emit('operation', trial=self.key, scenario=self.scenario,
                              config=self.config, **result)
        return result

    def finish(self):
        w1, r1, r2, w2 = (self.ops.get(k) for k in ('W1','R1','R2','W2'))
        ok = lambda x: bool(x and x['status']=='ok')
        checks = {k:None for k in ('RYW','MR','MW','WFR')}
        # True means a witnessed violation, False an eligible check with no violation.
        later_reads = [r for r in (r1,r2) if ok(r) and ok(w1)
                       and r['invocation_ns'] >= w1['completion_ns']]
        if later_reads: checks['RYW'] = any(r['value']['a'] < 1 for r in later_reads)
        if ok(r1) and ok(r2): checks['MR'] = r2['value']['a'] < r1['value']['a']
        if ok(w1) and ok(w2): checks['MW'] = w2['value']['a'] < 1
        # W2 must incorporate every preceding observed version, even after a regressing read.
        preceding = [r for r in (r1,r2) if ok(r) and w2 and r['completion_ns'] < w2['invocation_ns']]
        prior = max(preceding,key=lambda r:r['value']['a']) if preceding else None
        if ok(prior) and ok(w2): checks['WFR'] = w2['value']['a'] < prior['value']['a']
        for s in self.sessions:
            s.end_session()
        row = dict(trial=self.key, scenario=self.scenario, config=self.config,
                   checks=checks, operations=self.ops)
        self.cluster.log.emit('trial', **row)
        return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work-dir', type=Path, required=True, help='New, non-existing directory for disposable data')
    ap.add_argument('--out', type=Path, required=True, help='New, non-existing results directory')
    ap.add_argument('--normal', type=int, default=20)
    ap.add_argument('--lag', type=int, default=10)
    ap.add_argument('--failure', type=int, default=10)
    ap.add_argument('--fault-repeats', type=int, default=10)
    ap.add_argument('--base-port', type=int, default=29101)
    ap.add_argument('--seed', type=int, default=419)
    args = ap.parse_args()
    if any(getattr(args, name) < 0 for name in ('normal', 'lag', 'failure', 'fault_repeats')):
        ap.error('scenario repetition counts must be non-negative')
    from .docker_backend import DockerCluster
    DockerCluster.preflight()
    args.work_dir = args.work_dir.resolve()
    args.out = args.out.resolve()
    args.work_dir.mkdir(parents=True, exist_ok=False)
    args.out.mkdir(parents=True, exist_ok=False)
    log = Log(args.out/'history.jsonl')
    cluster = DockerCluster(args.work_dir, log, args.base_port)
    rows = []
    rng = random.Random(args.seed)
    repo_root = Path(__file__).resolve().parents[1]
    source_files = {
        'lab.py': Path(__file__),
        'docker_backend.py': Path(__file__).with_name('docker_backend.py'),
        'compose.yaml': repo_root/'config'/'compose.yaml',
        'Dockerfile': repo_root/'config'/'Dockerfile',
    }
    meta = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                python=platform.python_version(), pymongo=pymongo.version,
                platform=platform.platform(), mongod='pending container startup',
                deployment_type='docker-compose',
                source_sha256={name:hashlib.sha256(path.read_bytes()).hexdigest()
                               for name,path in source_files.items()},
                configs=CONFIGS, arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
                timeouts=dict(read_ms=MAX_READ_MS, socket_ms=SOCKET_TIMEOUT_MS,
                              write_ms=WRITE_TIMEOUT_MS), status='running')
    (args.out/'metadata.json').write_text(json.dumps(meta, indent=2))
    try:
        cluster.start()
        meta['mongod']='db version v'+cluster.info['server_build']['version']
        meta['deployment']=cluster.info
        (args.out/'metadata.json').write_text(json_util.dumps(meta,indent=2))
        cluster.snapshot('initialized')
        for scenario, n in [('normal',args.normal),('replication_lag',args.lag),('secondary_crash',args.failure)]:
            if n == 0:
                continue
            jobs = [(cfg,i) for cfg in CONFIGS for i in range(n)]
            rng.shuffle(jobs)
            ids = [f'{scenario}-{cfg}-{i}' for cfg,i in jobs]
            cluster.seed(ids)
            if scenario=='replication_lag': cluster.delay(3)
            if scenario=='secondary_crash': cluster.stop_node(2, crash=True)
            p = cluster.primary()
            target = 1-p if scenario=='secondary_crash' else 2
            for cfg,i in jobs:
                t = Trial(cluster,f'{scenario}-{cfg}-{i}',scenario,cfg)
                for label,node in [('W1',p),('R1',p),('R2',target),('W2',p)]: t.op(label,node)
                rows.append(t.finish())
            if scenario=='replication_lag': cluster.delay(0)
            if scenario=='secondary_crash':
                cluster.start_node(2)
                wait_for(lambda: cluster.hello(2).get('secondary'),30)
            cluster.barrier(f'end-{scenario}')
            cluster.snapshot(scenario)
            print(f'Completed {scenario}: {len(jobs)} histories',flush=True)

        # Network-only scenario: all mongod processes stay alive throughout.
        # Each config is tested in its own partition to avoid order confounding.
        for scenario in ['primary_crash','network_partition_2_1','network_partition','partition_rollback']:
            jobs = [(cfg,i) for cfg in CONFIGS for i in range(args.fault_repeats)]
            rng.shuffle(jobs)
            for cfg,i in jobs:
                key=f'{scenario}-{cfg}-{i}'
                cluster.seed([key])
                p=cluster.primary()
                target=1-p
                t=Trial(cluster,key,scenario,cfg)
                if scenario == 'network_partition_2_1':
                    majority=cluster.mesh.split_two_one(p)
                    # The isolated old primary must step down; the two-node side
                    # retains a voting majority and elects its eligible member.
                    wait_for(lambda: not cluster.hello(p).get('isWritablePrimary'),40)
                    newp=cluster.primary(exclude=p)
                    t.op('W1',newp)
                    t.op('R1',newp)
                    t.op('R2',p)
                    t.op('W2',newp)
                    t.op('W_unavailable',p)
                    cluster.snapshot(key+'-isolated')
                    cluster.mesh.set_enabled(True)
                    cluster.primary()
                else:
                    if scenario != 'primary_crash': cluster.mesh.set_enabled(False)
                    t.op('W1',p)
                    t.op('R1',p)
                if scenario=='primary_crash':
                    # A healthy-replication failover; no artificial durability barrier after W1.
                    cluster.stop_node(p,crash=True)
                    newp=cluster.primary(exclude=p)
                    t.op('R2',newp)
                    t.op('W2',newp)
                    cluster.start_node(p)
                elif scenario=='network_partition':
                    t.op('R2',target)
                    t.op('W2',p)
                    # Establish sustained quorum loss in addition to the transient window.
                    wait_for(lambda: not cluster.hello(p).get('isWritablePrimary'),40)
                    t.op('W_unavailable',p)
                    cluster.snapshot(key+'-isolated')
                    cluster.mesh.set_enabled(True)
                    cluster.primary()
                elif scenario=='partition_rollback':
                    # Firewall rules prevent W1 replication. Kill old primary, then
                    # heal surviving nodes; W2 executes on an independently elected branch.
                    cluster.stop_node(p,crash=True)
                    cluster.mesh.set_enabled(True)
                    newp=cluster.primary(exclude=p)
                    # Test WFR immediately after R1 and before a new read can change its dependency.
                    t.op('W2',newp)
                    t.op('R2',newp)
                    cluster.start_node(p)
                row=t.finish()
                rows.append(row)
                cluster.barrier(key+'-healed')
                # Observe all replicas after healing; retain evidence of rollback/retention.
                for node,c in enumerate(cluster.clients):
                    value=c.lab.records.with_options(read_preference=ReadPreference.SECONDARY_PREFERRED).find_one({'_id':key})
                    log.emit('healed_value', trial=key,node=node,value=value)
                print(f'Completed {key}: {row["checks"]}',flush=True)
        meta['status']='complete'
    except BaseException:
        meta['status']='failed'
        raise
    finally:
        try:
            cluster.close()
        except Exception as cleanup_error:
            meta['cleanup_error']=str(cleanup_error)
            meta['status']='failed'
        meta['finished_utc']=datetime.now(timezone.utc).isoformat()
        (args.out/'metadata.json').write_text(json_util.dumps(meta,indent=2))
        (args.out/'trials.json').write_text(json_util.dumps(rows,indent=2))
        for path in args.work_dir.glob('mongod-*.log'):
            shutil.copy2(path,args.out/path.name)
        log.f.close()
    if meta['status'] != 'complete':
        raise SystemExit('Run failed during cleanup; inspect metadata.json before analyzing results')
    print(f'Results: {args.out}',flush=True)


if __name__=='__main__':
    main()
