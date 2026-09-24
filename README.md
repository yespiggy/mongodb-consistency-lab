# MongoDB client-centric consistency lab

This repository contains the code and raw evidence for a three-member MongoDB replica-set experiment. It tests read-your-writes (RYW), monotonic reads (MR), monotonic writes (MW), and writes-follow-reads (WFR) under eight client configurations and seven operating scenarios. The PDF report is submitted separately.

## Repository layout

| Path | Contents |
|---|---|
| `source/` | Experiment runner, workload, consistency checker, Docker backend, and analyzer |
| `config/` | Docker Compose file, Dockerfile, and pinned Python dependencies |
| `tests/` | Eight synthetic checker tests |
| `results/MEASURED_RESULTS.md` | Summary of the formal run |
| `data/` | Formal raw-data ZIP, manifest, and archive instructions |

All commands below run **from the repository root**. The runner builds the image and creates its own Docker Compose project, containers, network, and named volumes. Do not start Compose separately before a run. Every run needs new, non-existing work and output directories.

## Prerequisites and setup

Install Python 3.13, Docker Engine with Compose (Docker Desktop on macOS or Windows), and start the Docker engine. The measured run used MongoDB 7.0.32, PyMongo 4.10.1, and Python 3.13.1. Docker must allow Linux containers with `NET_ADMIN`, because the network-partition scenarios use container-local `iptables` rules.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r config/requirements.txt
.venv/bin/python -m unittest -v tests.test_checker
docker compose -f config/compose.yaml config --quiet
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`. The first run may need to download the MongoDB image and build the lab image.

## Quick execution check

This small run starts the three-node replica set and exercises all eight configurations under normal operation. It produces 8 histories and 32 application operations; it does **not** test fault injection.

```bash
.venv/bin/python -m source.run --work-dir work/smoke-01 \
  --out results/runs/smoke-01 \
  --normal 1 --lag 0 --failure 0 --fault-repeats 0
.venv/bin/python -m source.analyze results/runs/smoke-01
```

Use different directory names for another run. If ports 29101–29103 are occupied, add `--base-port 30101` to the `source.run` command; the three chosen ports must be free.

## Full experiment

This command runs the complete seven-scenario matrix: 20 normal histories per configuration and 10 histories per configuration for each of six fault scenarios, for 640 histories total. It can take substantially longer than the quick check because faults require elections and recovery.

```bash
.venv/bin/python -m source.run --work-dir work/full-01 \
  --out results/runs/full-01 \
  --normal 20 --lag 10 --failure 10 --fault-repeats 10
.venv/bin/python -m source.analyze results/runs/full-01
```

The scenarios are normal operation, a three-second delayed replica, secondary crash, primary crash and election, a 2+1 network partition, complete 1+1+1 isolation, and partition followed by failover and rollback. Crashes use SIGKILL. Network partitions block only peer-container traffic, leaving the host controller connected through published loopback ports. The runner heals partitions, collects MongoDB logs, and stops its containers when it finishes. It retains named volumes for inspection.

The client matrix varies causal tracking (off/on), read concern (`local`/`majority`), and write concern (`w:1`/`w:majority`). A/B, C/D, E/F, and G/H are matched pairs that differ only in causal tracking. Measured read, socket, and write-concern deadlines are 5000, 7000, and 5000 ms. The random seed defaults to 419.

## Inspect the supplied formal results

The archived run from 22 September 2026 contains 640 histories and 2720 attempted operations. Its summary is [results/MEASURED_RESULTS.md](results/MEASURED_RESULTS.md). The complete event history, trial records, metadata, audit, and three MongoDB server logs are in [data/matrix8-timeout5s-full-20260922-raw.zip](data/matrix8-timeout5s-full-20260922-raw.zip). See [data/RAW_DATA.md](data/RAW_DATA.md) and [data/RAW_DATA_MANIFEST.json](data/RAW_DATA_MANIFEST.json) for contents and checksums.

To regenerate the summary and audit from the archive:

```bash
python3 -m zipfile -e data/matrix8-timeout5s-full-20260922-raw.zip tmp/raw-verification
.venv/bin/python -m source.analyze tmp/raw-verification
```

The analyzer should report 640 histories, 2720 attempted operations, 2700 monitored commands, 20 pre-command errors, 160 isolation snapshots, and no command-parameter, wire-coverage, or isolation audit failures. A cell in the results counts violations / eligible checks. A failed prerequisite makes a check inconclusive; zero observed violations do not establish a universal guarantee. The rollback checks use the durable-history interpretation described in the report.

The archive records SHA-256 hashes of the source files used for the formal run. That run used the original flat repository layout at [commit `b3b3d95`](https://github.com/yespiggy/mongodb-consistency-lab/tree/b3b3d95b3908232af34d01752c47f58403ce8926). This submission branch groups the code under `source/` and `config/` and allows zero repetitions for an omitted smoke-test scenario, so its source-file hashes differ from the archived metadata. The default full experiment and its workload and consistency checker are unchanged.

## Inspect or remove a newly created run

The work directory contains `compose-project.txt`, which identifies the run's Docker Compose project. For the full-run example above:

```bash
LAB_PROJECT=$(cat work/full-01/compose-project.txt)
docker compose -f config/compose.yaml -p "$LAB_PROJECT" ps -a
```

When those containers and their database volumes are no longer needed, remove **only that run's project** with:

```bash
docker compose -f config/compose.yaml -p "$LAB_PROJECT" down --volumes
```

The experiment uses three Docker containers on one physical host, as permitted by the assignment. These containers do not provide independent host, disk, kernel, or power failure domains. Direct connections intentionally select read targets; this is not a measurement of normal driver server selection.

## Sources and AI usage

- [MongoDB causal consistency and read/write concerns](https://www.mongodb.com/docs/v7.0/core/causal-consistency-read-write-concerns/)
- [MongoDB read isolation and consistency](https://www.mongodb.com/docs/v7.0/core/read-isolation-consistency-recency/)
- [MongoDB replica-set rollbacks](https://www.mongodb.com/docs/v7.0/core/replica-set-rollbacks/)
- [PyMongo sessions](https://pymongo.readthedocs.io/en/4.10.1/api/pymongo/client_session.html)
- [Docker Compose services](https://docs.docker.com/reference/compose-file/services/)

Codex and Claude Code assisted with interpretation, implementation, debugging, and documentation. The formal measurements came from real MongoDB executions. Group members should review the code and findings before submission.
