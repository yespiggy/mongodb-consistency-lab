# Measured results

Cells show violations / eligible checks; a dash means no eligible check. Timeouts are not violations.

| Scenario | Config | Histories | RYW | MR | MW | WFR | Operation errors |
|---|---|---:|---:|---:|---:|---:|---:|
| normal | D | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | B | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | C | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| normal | A | 20 | 0/20 | 0/20 | 0/20 | 0/20 | 0/80 |
| replication_lag | C | 10 | 0/10 | - | 0/10 | 0/10 | 10/40 |
| replication_lag | A | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| replication_lag | D | 10 | 0/10 | - | 0/10 | 0/10 | 10/40 |
| replication_lag | B | 10 | 10/10 | 10/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | B | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | C | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | A | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| secondary_crash | D | 10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/40 |
| primary_crash | C | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | A | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | B | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| primary_crash | D | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/12 |
| network_partition_2_1 | A | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition_2_1 | B | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition_2_1 | C | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition_2_1 | D | 3 | 0/3 | - | 0/3 | 0/3 | 6/15 |
| network_partition | D | 3 | - | - | - | - | 15/15 |
| network_partition | B | 3 | - | 0/3 | - | - | 9/15 |
| network_partition | A | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/15 |
| network_partition | C | 3 | - | - | 0/3 | - | 9/15 |
| partition_rollback | D | 3 | - | - | - | - | 6/12 |
| partition_rollback | C | 3 | 3/3 | - | 3/3 | - | 3/12 |
| partition_rollback | A | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 0/12 |
| partition_rollback | B | 3 | - | 0/3 | - | 0/3 | 3/12 |
