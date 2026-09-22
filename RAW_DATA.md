# Formal A--H measurements and detailed server logs

Download [matrix8-full-20260922-raw.zip](matrix8-full-20260922-raw.zip) for the complete, unmodified formal Docker run. The archive contains 416 histories and 1,712 application operations from 22 September 2026 across all eight A--H configurations and seven operating scenarios. Preliminary smoke tests are excluded. The earlier `docker-run-2026-09-17-raw.zip` is retained only as legacy evidence and uses obsolete configuration IDs.

| File | Contents |
|---|---|
| `history.jsonl` | Detailed event stream: application operations, actual driver commands, returned values/errors, causal tokens, faults, topology snapshots and post-recovery observations. |
| `trials.json` | Structured trial histories and the four consistency-check classifications. |
| `mongod-0.log`, `mongod-1.log`, `mongod-2.log` | Detailed MongoDB server logs collected from the three containers, including elections, replication, failures and rollback messages. |
| `metadata.json` | Execution times, software versions, parameters, source hashes and Docker deployment information. |
| `audit.json` | Command-parameter and network-isolation validation results. |
| `summary.json`, `summary.md` | Derived aggregate results, not substitutes for the raw histories. |

The MongoDB log files are server diagnostic logs, not a database volume backup or a packet capture. The archive is the complete set of files collected by this run; it does not claim to capture events the harness did not instrument.

## Verify and analyze

[RAW_DATA_MANIFEST.json](RAW_DATA_MANIFEST.json) records SHA-256 values for every original file and the ZIP. Extract the archive into a temporary directory, then analyze its `matrix8-full-01` directory:

```bash
mkdir -p tmp/raw-verification
python3 -m zipfile -e matrix8-full-20260922-raw.zip tmp/raw-verification
.venv/bin/python analyze.py tmp/raw-verification/matrix8-full-01
```

The analysis should report 416 histories, 1,712 operations/commands, 48 isolation snapshots and no parameter/isolation audit failures. Each consistency cell counts violations / eligible checks. Timeouts are not treated as stale-value violations.

The original metadata retains the measurement host's local paths and container identifiers for provenance. The repository is private. New locally generated `results/` directories and loose logs remain ignored by Git; this named, archived run is intentionally included.
