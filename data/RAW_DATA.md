# Formal A--H measurements and detailed server logs

Download [matrix8-timeout5s-full-20260922-raw.zip](matrix8-timeout5s-full-20260922-raw.zip) for the complete formal Docker run. The archive contains 640 histories and 2,720 attempted application operations from 22 September 2026 across all eight A--H configurations and seven operating scenarios. It uses 5000 ms read and write-concern deadlines and a 7000 ms socket timeout. Preliminary and interrupted runs are excluded.

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

[RAW_DATA_MANIFEST.json](RAW_DATA_MANIFEST.json) records SHA-256 values for every original file and the ZIP. From the repository root, extract the archive into a temporary directory, then analyze that directory:

```bash
mkdir -p tmp/raw-verification
python3 -m zipfile -e data/matrix8-timeout5s-full-20260922-raw.zip tmp/raw-verification
.venv/bin/python -m source.analyze tmp/raw-verification
```

The analysis should report 640 histories, 2,720 attempted operations, 2,700 wire commands, 20 pre-command availability errors, 160 isolation snapshots, and no parameter, wire-coverage, or isolation audit failures. Each consistency cell counts violations / eligible checks. Timeouts are not treated as stale-value violations.

The original metadata retains the measurement host's local paths and container identifiers for provenance. The repository is private. New locally generated `results/runs/` directories and loose logs remain ignored by Git; this named, archived run is intentionally included.
