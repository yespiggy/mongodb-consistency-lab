# Original measurements and detailed server logs

Download [docker-run-2026-09-17-raw.zip](docker-run-2026-09-17-raw.zip) for the complete, unmodified formal Docker run. The archive preserves the original directory and filenames. It contains 208 histories and 856 application operations from 17 September 2026, including the typical 2+1 partition; preliminary smoke tests and earlier native-process runs are excluded.

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

[RAW_DATA_MANIFEST.json](RAW_DATA_MANIFEST.json) records SHA-256 values for every original file and the ZIP. Extract the archive into `results/`, then run:

```bash
python3 -m zipfile -e docker-run-2026-09-17-raw.zip results
.venv/bin/python analyze.py results/docker-run-2026-09-17
```

Install dependencies as described in the main README first. The analysis should report 208 histories, 856 operations/commands, 24 isolation snapshots and no parameter/isolation audit failures. Each consistency cell counts violations / eligible checks. Timeouts are not treated as stale-value violations.

The original metadata retains the measurement host's local paths and container identifiers for provenance. The repository is private. New locally generated `results/` directories and loose logs remain ignored by Git; this named, archived run is intentionally included.
