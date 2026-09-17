# MongoDB client-centric consistency lab

A three-container MongoDB replica set for investigating read-your-writes, monotonic reads, monotonic writes, and writes-follow-reads consistency.

## Architecture

Docker Compose runs MongoDB 7.0.32 in three containers with separate IP addresses and data volumes. All members vote; mongo0 and mongo1 are electable, while mongo2 has priority 0. The host Python client uses ports 29101–29103 with direct connections and explicitly propagates causal session metadata.

## Run

Install and start Docker Desktop (or Docker Engine with Compose), then run from this directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_checker.py
.venv/bin/python run.py --work-dir work/smoke-01 --out results/smoke-01 --normal 1 --lag 1 --failure 1 --fault-repeats 1
.venv/bin/python analyze.py results/smoke-01
```

Windows uses `.venv\Scripts\python.exe`. The first run downloads and builds the container image. Do not manually run Compose before the experiment: the runner creates its own project and fresh volumes. Use a new work/output directory each time.

Full experiment and report generation:

```bash
.venv/bin/python run.py --work-dir work/full-01 --out results/full-01
.venv/bin/python analyze.py results/full-01
.venv/bin/python make_report.py results/full-01 --out report.pdf
```

The default run contains 196 histories and 796 application operations. Use `--base-port 30101` if the default ports are occupied. The runner heals the network and stops its containers after collecting evidence, retaining their volumes.

## Configurations

| ID | Causal tracking | Read concern | Write concern |
|---|---|---|---|
| A | off | local | 1 |
| B | off | majority | majority |
| C | on | majority | 1 |
| D | on | majority | majority |

Scenarios: normal operation, 3-second replica lag, secondary crash, primary crash, complete 1+1+1 network partition, and partition followed by failover/rollback. Crash injection uses container SIGKILL. Partition injection uses container-local iptables with NET_ADMIN to block peer traffic while preserving host-client access. Election timeout is 15 seconds.

## Results and interpretation

The completed Docker run on 17 September 2026 passed the command-parameter and network-isolation audits. Its aggregate results are in [MEASURED_RESULTS.md](MEASURED_RESULTS.md). Seven checker unit tests passed.

Cells count violations / eligible checks. Timeouts are operation errors, not stale-value violations; missing successful prerequisites make checks inconclusive. RYW/MW rollback checks use an explicitly durable-history interpretation. Zero observed violations do not prove a universal guarantee.

Raw measurements, server logs and the submitted report remain in the separately delivered project archive. They are not bundled into this code repository. New runs generate their own evidence in `results/` and a PDF through `make_report.py`.

## Inspect and clean up a run

```bash
LAB_PROJECT=$(cat work/full-01/compose-project.txt)
docker compose -p "$LAB_PROJECT" ps -a
docker compose -p "$LAB_PROJECT" start
docker compose -p "$LAB_PROJECT" stop
```

To delete only that experiment and its database volumes when no longer needed:

```bash
docker compose -p "$LAB_PROJECT" down --volumes
```

All containers share the physical host and, on Docker Desktop, the Linux VM. This is the assignment's multiple-containers-on-one-machine deployment option, not independent physical fault domains. The network experiments test 1+1+1 partitions, not a 2+1 split. The visible, voting delayed member is a laboratory control.

## Sources and AI usage

- [MongoDB causal consistency guarantees](https://www.mongodb.com/docs/v7.0/core/causal-consistency-read-write-concerns/)
- [MongoDB read isolation and consistency](https://www.mongodb.com/docs/v7.0/core/read-isolation-consistency-recency/)
- [MongoDB replica-set rollbacks](https://www.mongodb.com/docs/v7.0/core/replica-set-rollbacks/)
- [PyMongo sessions](https://pymongo.readthedocs.io/en/4.10.1/api/pymongo/client_session.html)
- [Docker Desktop installation](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Compose services](https://docs.docker.com/reference/compose-file/services/)

OpenAI Codex assisted with design, implementation, debugging, local execution, analysis, documentation and repository preparation during September 2026. Measurements were produced by real MongoDB executions. Group members should review the code and findings before submission.
