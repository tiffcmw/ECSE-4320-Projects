| setup | IOPS (sd) | mean µs (sd) | p99 µs (sd) | configured QD | effective QD (Little) |
|---|---|---|---|---|---|
| A: direct=1, QD1 (correct) | 14,540 (230) | 68.63 (1.06) | 81.41 (2.05) | 1 | 1.00 |
| B: direct=0 buffered, QD1 (flawed: page cache) | 1,316,919 (79,092) | 0.69 (0.05) | 1.00 (0.00) | 1 | 0.90 |
| C: direct=1, QD16 (correct) | 191,798 (504) | 83.19 (0.21) | 125.10 (0.59) | 16 | 15.96 |
| D: psync with iodepth=64 (flawed: depth ignored) | 14,395 (42) | 69.35 (0.20) | 81.75 (1.56) | 64 | 1.00 |
