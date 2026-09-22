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

Full experiment and analysis:

```bash
.venv/bin/python run.py --work-dir work/full-01 --out results/full-01
.venv/bin/python analyze.py results/full-01
```

The submission report source is `report/main.tex`. Compile it with Tectonic or a standard
LaTeX installation after updating the group-member line on the title page.

With the eight-configuration matrix, the default run contains 640 histories: 20 normal histories per configuration and 10 per configuration in every other scenario. Measured read, socket, and write-concern timeouts are 5000, 7000, and 5000 ms. Use `--base-port 30101` if the default ports are occupied. The runner heals the network and stops its containers after collecting evidence, retaining their volumes.

## Configurations

| ID | Causal tracking | Read concern | Write concern |
|---|---|---|---|
| A | off | local | 1 |
| B | on | local | 1 |
| C | off | local | majority |
| D | on | local | majority |
| E | off | majority | 1 |
| F | on | majority | 1 |
| G | off | majority | majority |
| H | on | majority | majority |

The rows form four adjacent matched causal-session pairs: A/B (`local`, `w:1`), C/D (`local`, `majority`), E/F (`majority`, `w:1`), and G/H (`majority`, `majority`). Within each pair, causal tracking is the only changed factor. Configurations B, D, F, and H reproduce the four read-concern/write-concern combinations from MongoDB's causal-consistency table; A, C, E, and G are their non-causal controls.

Scenarios: normal operation, 3-second replica lag, secondary crash, primary crash, a typical 2+1 network partition, complete 1+1+1 isolation, and partition followed by failover/rollback. Crash injection uses container SIGKILL. Partition injection uses container-local iptables with NET_ADMIN to block peer traffic while preserving host-client access. In the 2+1 experiment the current primary is isolated, the two-node majority elects a new primary and remains writable, and the client probes both sides. Election timeout is 15 seconds.

## Results and interpretation

The formal A--H Docker run completed on 22 September 2026 with 640 histories and 2,720 attempted operations. Command monitoring captured 2,700 wire commands; 20 rollback operations were rejected by PyMongo before transmission while restarted direct connections temporarily reported no session capability. The run passed all command-parameter, wire-coverage, and network-isolation audits. Its aggregate results are in [MEASURED_RESULTS.md](MEASURED_RESULTS.md). Eight checker unit tests passed.

Cells count violations / eligible checks. Timeouts are operation errors, not stale-value violations; missing successful prerequisites make checks inconclusive. RYW/MW rollback checks use an explicitly durable-history interpretation. Zero observed violations do not prove a universal guarantee.

The complete formal measurements and detailed logs for all three MongoDB nodes are included in [the 5-second-timeout A--H raw-data archive](matrix8-timeout5s-full-20260922-raw.zip). See [RAW_DATA.md](RAW_DATA.md) for its contents and analysis commands, and [RAW_DATA_MANIFEST.json](RAW_DATA_MANIFEST.json) for SHA-256 checksums. Earlier archives are retained only as legacy evidence. New runs generate their own evidence in `results/`.

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

All containers share the physical host and, on Docker Desktop, the Linux VM. This is the assignment's multiple-containers-on-one-machine deployment option, not independent physical fault domains. The network experiments include both a 2+1 split and complete 1+1+1 isolation. The visible, voting delayed member is a laboratory control.

## Sources and AI usage

- [MongoDB causal consistency guarantees](https://www.mongodb.com/docs/v7.0/core/causal-consistency-read-write-concerns/)
- [MongoDB read isolation and consistency](https://www.mongodb.com/docs/v7.0/core/read-isolation-consistency-recency/)
- [MongoDB replica-set rollbacks](https://www.mongodb.com/docs/v7.0/core/replica-set-rollbacks/)
- [PyMongo sessions](https://pymongo.readthedocs.io/en/4.10.1/api/pymongo/client_session.html)
- [Docker Desktop installation](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Compose services](https://docs.docker.com/reference/compose-file/services/)

OpenAI Codex assisted with design, implementation, debugging, local execution, analysis, documentation and repository preparation during September 2026. Measurements were produced by real MongoDB executions. Group members should review the code and findings before submission.
