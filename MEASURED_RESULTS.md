# Formal A-H measured results

Run: `results/matrix8-timeout5s-full-02`, 22 September 2026. The audit reports 640 histories, 2,720 attempted operations, 2,700 wire commands, 20 pre-command availability errors, 160 isolation snapshots, unique trial IDs, and no command-parameter, wire-coverage, or isolation failures.

Cells show violations / eligible checks; a dash means no eligible check. Errors are availability outcomes, not consistency violations.

| Scenario | Config | Causal | Read | Write | Histories | RYW | MR | MW | WFR | Errors |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| normal | A | off | local | 1 | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | B | on | local | 1 | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | C | off | local | majority | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | D | on | local | majority | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | E | off | majority | 1 | 20 | 20/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | F | on | majority | 1 | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | G | off | majority | majority | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | H | on | majority | majority | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| replication_lag | A | off | local | 1 | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | B | on | local | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | C | off | local | majority | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | D | on | local | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | E | off | majority | 1 | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | F | on | majority | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | G | off | majority | majority | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | H | on | majority | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | A | off | local | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | B | on | local | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | C | off | local | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | D | on | local | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | E | off | majority | 1 | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | F | on | majority | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | G | off | majority | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | H | on | majority | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | A | off | local | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | B | on | local | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | C | off | local | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | D | on | local | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | E | off | majority | 1 | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | F | on | majority | 1 | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | G | off | majority | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | H | on | majority | majority | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| network_partition_2_1 | A | off | local | 1 | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 10/50 |
| network_partition_2_1 | B | on | local | 1 | 10 | 0/10 | - | 0/10 | 0/10 | 20/50 |
| network_partition_2_1 | C | off | local | majority | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 10/50 |
| network_partition_2_1 | D | on | local | majority | 10 | 0/10 | - | 0/10 | 0/10 | 20/50 |
| network_partition_2_1 | E | off | majority | 1 | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 10/50 |
| network_partition_2_1 | F | on | majority | 1 | 10 | 0/10 | - | 0/10 | 0/10 | 20/50 |
| network_partition_2_1 | G | off | majority | majority | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 10/50 |
| network_partition_2_1 | H | on | majority | majority | 10 | 0/10 | - | 0/10 | 0/10 | 20/50 |
| network_partition | A | off | local | 1 | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 10/50 |
| network_partition | B | on | local | 1 | 10 | 0/10 | - | 0/10 | 0/10 | 20/50 |
| network_partition | C | off | local | majority | 10 | - | 10/10 | - | - | 30/50 |
| network_partition | D | on | local | majority | 10 | - | - | - | - | 40/50 |
| network_partition | E | off | majority | 1 | 10 | 10/10 | 0/10 | 0/10 | 0/10 | 10/50 |
| network_partition | F | on | majority | 1 | 10 | - | - | 0/10 | - | 30/50 |
| network_partition | G | off | majority | majority | 10 | - | 0/10 | - | - | 30/50 |
| network_partition | H | on | majority | majority | 10 | - | - | - | - | 50/50 |
| partition_rollback | A | off | local | 1 | 10 | 10/10 | 10/10 | 10/10 | 10/10 | 0/40 |
| partition_rollback | B | on | local | 1 | 10 | 6/7 | 6/6 | 6/6 | 6/6 | 8/40 |
| partition_rollback | C | off | local | majority | 10 | - | 9/9 | - | 7/7 | 14/40 |
| partition_rollback | D | on | local | majority | 10 | - | 9/9 | - | 3/3 | 18/40 |
| partition_rollback | E | off | majority | 1 | 10 | 9/9 | 0/8 | 8/8 | 0/8 | 4/40 |
| partition_rollback | F | on | majority | 1 | 10 | 7/7 | - | 9/9 | - | 14/40 |
| partition_rollback | G | off | majority | majority | 10 | - | 0/10 | - | 0/6 | 14/40 |
| partition_rollback | H | on | majority | majority | 10 | - | - | - | - | 34/40 |
