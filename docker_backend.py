"""Docker lifecycle and real network partitions; workload/checker live in lab.py."""
import json
import os
import shutil
import socket
import subprocess
import uuid
from pathlib import Path

from lab import Cluster, wait_for


class ContainerHandle:
    def __init__(self):
        self.running = True

    def poll(self):
        return None if self.running else 137


class DockerPartition:
    def __init__(self, cluster):
        self.cluster = cluster
        self.addresses = cluster.addresses()
        self.enabled = True
        for i in range(3):
            cluster.compose('exec', '-T', '--user', 'root', f'mongo{i}',
                            'sh', '-eu', '-c',
                            'iptables -N CC_LAB_IN; iptables -N CC_LAB_OUT; '
                            'iptables -I INPUT 1 -j CC_LAB_IN; iptables -I OUTPUT 1 -j CC_LAB_OUT')

    def set_groups(self, groups, label):
        """Allow traffic within each group and drop traffic between groups."""
        group_for = {node: group for group, nodes in enumerate(groups) for node in nodes}
        if set(group_for) != {0, 1, 2}:
            raise ValueError(f'Partition groups must contain nodes 0, 1, and 2 exactly once: {groups}')
        # A complete cycle includes all live containers. After a node restart its
        # network namespace/rules may reset, so create chains again if necessary.
        for i in range(3):
            if not self.cluster.procs[i] or self.cluster.procs[i].poll() is not None:
                continue
            commands = [
                'iptables -N CC_LAB_IN 2>/dev/null || true',
                'iptables -N CC_LAB_OUT 2>/dev/null || true',
                'iptables -C INPUT -j CC_LAB_IN 2>/dev/null || iptables -I INPUT 1 -j CC_LAB_IN',
                'iptables -C OUTPUT -j CC_LAB_OUT 2>/dev/null || iptables -I OUTPUT 1 -j CC_LAB_OUT',
                'iptables -F CC_LAB_IN', 'iptables -F CC_LAB_OUT',
            ]
            if len(groups) > 1:
                for j, address in enumerate(self.addresses):
                    if i != j and group_for[i] != group_for[j]:
                        commands += [f'iptables -A CC_LAB_IN -s {address} -j DROP',
                                     f'iptables -A CC_LAB_OUT -d {address} -j DROP']
            commands += ['iptables -S CC_LAB_IN', 'iptables -S CC_LAB_OUT']
            rules=self.cluster.compose('exec','-T','--user','root',f'mongo{i}',
                                       'sh','-eu','-c','; '.join(commands))
            self.cluster.log.emit('firewall_rules',node=i,rules=rules)
        self.enabled=len(groups) == 1
        self.cluster.log.emit('network',enabled=self.enabled,partition=label,groups=groups,
                              mechanism='container INPUT/OUTPUT peer-IP DROP',addresses=self.addresses)
        # A partition must not accidentally remove the application's access.
        for i,p in enumerate(self.cluster.procs):
            if p and p.poll() is None:
                self.cluster.clients[i].admin.command('ping')

    def set_enabled(self, enabled):
        groups=[[0,1,2]] if enabled else [[0],[1],[2]]
        self.set_groups(groups, 'healed' if enabled else '1+1+1')

    def split_two_one(self, minority):
        majority=[i for i in range(3) if i != minority]
        self.set_groups([majority,[minority]],'2+1')
        return majority

    def close(self):
        pass


class DockerCluster(Cluster):
    def __init__(self, work, log, base=29101):
        super().__init__(work,log,base)
        self.directory=Path(__file__).resolve().parent
        self.project='cc-lab-'+uuid.uuid4().hex[:10]
        self.env=dict(os.environ, **{f'LAB_PORT{i}':str(base+i) for i in range(3)})
        self.created=False
        self.info={}

    def compose(self,*args,timeout=180):
        command=['docker','compose','--project-name',self.project,
                 '--file',str(self.directory/'compose.yaml'),*args]
        result=subprocess.run(command,env=self.env,text=True,stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,timeout=timeout)
        if result.returncode:
            raise RuntimeError(f'Docker command failed: {command}\n{result.stdout}')
        return result.stdout

    @staticmethod
    def preflight():
        if not shutil.which('docker'):
            raise SystemExit('Docker is not installed/on PATH. Install and start Docker Desktop, then retry.')
        for command in [['docker','info'],['docker','compose','version']]:
            r=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
            if r.returncode:
                raise SystemExit('Start Docker Desktop and wait until its engine is running.\n'+r.stdout)

    def addresses(self):
        result=[]
        for i in range(3):
            cid=self.compose('ps','-q',f'mongo{i}').strip()
            info=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
            addresses=[v['IPAddress'] for v in info['NetworkSettings']['Networks'].values()]
            if len(addresses)!=1:
                raise RuntimeError('Expected exactly one isolated lab network per MongoDB container')
            # Validate before placing Docker-reported data in shell arguments.
            import ipaddress
            result.append(str(ipaddress.IPv4Address(addresses[0])))
        return result

    def start(self):
        self.preflight()
        for port in self.back:
            with socket.socket() as s:
                s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                s.bind(('127.0.0.1',port))
        print('Building the MongoDB lab image (first run downloads layers)...',flush=True)
        self.compose('build',timeout=900)
        # Unique project name ensures new containers AND new volumes every run.
        (self.work/'compose-project.txt').write_text(self.project+'\n')
        self.created=True
        self.compose('up','-d',timeout=180)
        self.procs=[ContainerHandle() for _ in range(3)]
        self.make_clients()
        for c in self.clients:
            wait_for(lambda c=c:c.admin.command('ping'),90)
        cfg=dict(_id='cc_lab',members=[dict(_id=i,host=f'mongo{i}:27017',
                  priority=0 if i==2 else 1,hidden=False,votes=1) for i in range(3)],
                  settings=dict(electionTimeoutMillis=15000,heartbeatIntervalMillis=500))
        self.clients[0].admin.command('replSetInitiate',cfg)
        self.primary()
        wait_for(lambda: all(self.hello(i).get('isWritablePrimary') or self.hello(i).get('secondary')
                             for i in range(3)),90)
        for c in self.clients:c.close()
        self.make_clients()
        for c in self.clients:
            def ready(c=c):
                with c.start_session(causal_consistency=True) as s:
                    return c.admin.command('ping',session=s)
            wait_for(ready,30)
        self.mesh=DockerPartition(self)
        ids=[self.compose('ps','-q',f'mongo{i}').strip() for i in range(3)]
        containers=json.loads(subprocess.check_output(['docker','inspect',*ids],text=True))
        self.info=dict(type='docker-compose',project=self.project,
                       docker_version=subprocess.check_output(['docker','version','--format','{{json .}}'],text=True),
                       compose_version=self.compose('version').strip(),
                       resolved_compose=self.compose('config'),
                       containers=[dict(id=c['Id'],image_id=c['Image'],name=c['Name'],
                                        networks=c['NetworkSettings']['Networks'],mounts=c['Mounts']) for c in containers],
                       server_build=self.clients[self.primary()].admin.command('buildInfo'))
        self.log.emit('initial_config',config=self.clients[self.primary()].admin.command('replSetGetConfig'))
        self.log.emit('docker_deployment',**self.info)

    def start_node(self,i):
        self.compose('start',f'mongo{i}')
        self.procs[i]=ContainerHandle()
        self.log.emit('node_start',node=i,container=f'mongo{i}',project=self.project)

    def stop_node(self,i,crash=False):
        if self.procs[i] and self.procs[i].poll() is None:
            self.compose(*(['kill','--signal','SIGKILL'] if crash else ['stop','--timeout','20']),f'mongo{i}')
            self.procs[i].running=False
            self.log.emit('node_stop',node=i,crash=crash,container=f'mongo{i}',project=self.project)

    def close(self):
        # Collect logs even when setup or a trial failed. Keep this run's volumes
        # for review; remove them only with the explicit command in the README.
        try:
            if self.mesh:self.mesh.set_enabled(True)
        finally:
            for c in self.clients:c.close()
            if self.created:
                try:
                    self.compose('stop','--timeout','20',timeout=100)
                finally:
                    for i in range(3):
                        try:
                            logs=self.compose('logs','--no-color','--no-log-prefix',f'mongo{i}')
                            (self.work/f'mongod-{i}.log').write_text(logs)
                        except Exception as e:
                            self.log.emit('log_collection_error',node=i,error=str(e))
