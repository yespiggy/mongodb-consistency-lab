# Formal A-H measured results

Run: `results/matrix8-full-01`, 22 September 2026. The audit reports 416 histories, 1,712 operations and wire commands, 48 isolation snapshots, unique trial IDs, and no command-parameter or isolation failures.

Configuration pairs: A/B = `local,w:1`; C/D = `local,majority`; E/F = `majority,w:1`; G/H = `majority,majority`. The first member of each pair is non-causal and the second is causal.

Cells show violations / eligible checks; a dash means no eligible check. Timeouts are operation errors, not consistency violations.

| Scenario | Config | Histories | RYW | MR | MW | WFR | Operation errors |
|---|---|---:|---:|---:|---:|---:|---:|
| normal | A | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | B | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | C | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | D | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | E | 20 | 16/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | F | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | G | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | H | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| replication_lag | A | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | B | 10 | 0/10 | - | 0/10 | 0/10 | 10/40 |
| replication_lag | C | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | D | 10 | 0/10 | - | 0/10 | 0/10 | 10/40 |
| replication_lag | E | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | F | 10 | 0/10 | - | 0/10 | 0/10 | 10/40 |
| replication_lag | G | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | H | 10 | 0/10 | - | 0/10 | 0/10 | 10/40 |
| secondary_crash | A | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | B | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | C | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | D | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | E | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | F | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | G | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | H | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | A | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | B | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | C | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | D | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | E | 3 | 3/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | F | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | G | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | H | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| network_partition_2_1 | A | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition_2_1 | B | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition_2_1 | C | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition_2_1 | D | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition_2_1 | E | 3 | 3/3 | 0/3 | 0/3 | 0/3 | 3/15 |
| network_partition_2_1 | F | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition_2_1 | G | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition_2_1 | H | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition | A | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition | B | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition | C | 3 | - | 3/3 | - | - | 9/15 |
| network_partition | D | 3 | - | - | - | - | 12/15 |
| network_partition | E | 3 | 3/3 | 0/3 | 0/3 | 0/3 | 3/15 |
| network_partition | F | 3 | - | - | 0/3 | - | 9/15 |
| network_partition | G | 3 | - | 0/3 | - | - | 9/15 |
| network_partition | H | 3 | - | - | - | - | 15/15 |
| partition_rollback | A | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 0/12 |
| partition_rollback | B | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 0/12 |
| partition_rollback | C | 3 | - | 3/3 | - | 3/3 | 3/12 |
| partition_rollback | D | 3 | - | 3/3 | - | 3/3 | 3/12 |
| partition_rollback | E | 3 | 3/3 | 0/3 | 3/3 | 0/3 | 0/12 |
| partition_rollback | F | 3 | 3/3 | - | 3/3 | - | 3/12 |
| partition_rollback | G | 3 | - | 0/3 | - | 0/3 | 3/12 |
| partition_rollback | H | 3 | - | - | - | - | 6/12 |
