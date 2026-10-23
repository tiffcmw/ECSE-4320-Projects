# Number trace for Project3_SSD_Report.docx

Tokens checked: 862 (versions, dates, times and label numbers removed first: versions ['26.5.2', '27.0.1']).

| Category | Count |
|---|---|
| whitelisted constant | 16 |
| small integer (structural) | 473 |
| data (3+ significant digits) | 245 |
| derived formula | 105 |
| data, low precision (hand review) | 23 |
| **UNTRACED** | **0** |

## Untraced numbers

none

## Traced by derived formula or constant (token: source)

- 3.43: constant: fio version (health log)
- 4320: constant: course
- 2.2: derived: exp5 mid p99.9/p50, fio cores used (exp4 A psync16)
- 11.0: derived: exp6b mean 10-15 s GB/s
- 0.01: derived: exp7 buffered GB/s, exp7 buffered / best real IOPS, exp4 A psync QD8/QD1, exp4 A psync QD16/QD1, exp4 A plateau latency ms, exp4 B plateau latency ms,
- 1.5: derived: stage exp12 rerun TB
- 0.5: derived: read 256K IOPS k, minutes between exp4 A and B psync16
- 0.0: derived: exp7 IOPS ratio buffered/direct, exp7 latency ratio direct/buffered, exp7 buffered GB/s, exp7 direct QD1 MB/s, exp7 buffered / best real IOPS, directi
- 0.6: derived: exp7 direct QD1 MB/s, exp4 A psync8 / A peak, exp4 B psync8 / B peak
- 1.8: derived: exp6a write range diff percent
- 134.9: derived: exp3 arithmetic blend 50/50 k
- 0.1: derived: exp7 IOPS ratio buffered/direct, exp7 latency ratio direct/buffered, exp7 buffered GB/s, exp7 direct QD1 MB/s, exp7 buffered / best real IOPS, directi
- 0.9: derived: exp7 IOPS ratio buffered/direct, directio latency ratio, 4K IOPS GB/s high, write/read ceiling percent (sustained 11.05)
- 1.2: derived: exp4 B plateau latency ms, exp1 randread p99/p50
- 1.0: derived: exp7 latency ratio direct/buffered, exp4 A psync16 / A peak, exp4 B psync16 / B peak
- 1.16: derived: exp4 B plateau latency ms, exp1 randread p99/p50
- 2.6: derived: exp1 randwrite p99/p50
- 2.5: derived: exp3 read mean ratio 50/50
- 326: derived: exp2 16x256KiB latency us
- 1.31: derived: exp2 16x1MiB latency ms
- 4.0: constant: PCIe generation label
- 7.9: constant: PCIe 4.0 x4 payload (public spec)
- 1.3: derived: exp2 16x1MiB latency ms, exp3 arithmetic blend 50/50 k, stage exp12 first pass TB
- 80.7: derived: exp3 harmonic 50/50 k
- 4.5: derived: exp3 read cost us
- 2.1: derived: exp4/4b max Little deviation percent, posixaio
- 18.0: derived: exp5 p50 rise percent QD4->16
- 2.0: derived: exp6b duration s
- 15.8: constant: PCIe 5.0 x4 payload (public spec)
- 335: derived: exp5 mid samples above p99.99
- 98.5: derived: exp4 A psync16 / A peak
- 98.7: derived: exp4 B psync16 / B peak
- 1.351: derived: exp4 A plateau latency ms
- 1.160: derived: exp4 B plateau latency ms
- 1.00: derived: exp7 latency ratio direct/buffered
- 7.6: derived: exp4 A psync QD8/QD1
- 13.1: derived: exp4 A psync QD16/QD1, exp6b burst percent
- 0.78: derived: 4K IOPS GB/s low
- 3.3: derived: exp2 16x256KiB latency us, exp5 mid samples above p99.9, exp5 mid samples above p99.99, exp6b 300s at measured rate TB
- 3,347: derived: exp5 mid samples above p99.9
- 12,979: derived: exp5 max ms (QD4, QD16)
- 2.20: derived: exp5 mid p99.9/p50
- 11.3: derived: exp5 knee samples above p99.9, exp5 knee samples above p99.99
- 11,277: derived: exp5 knee samples above p99.9
- 1.6: derived: exp5 knee p99/p50
- 6,133: derived: exp5 max ms QD16
- 2.39: derived: exp5 knee p99.9/p50
- 1.43: derived: exp5 mid p99/p50
- 0.3: derived: exp2 16x256KiB latency us, exp6a read range diff percent, exp5 mid samples above p99.99, exp5 p99 rise percent QD4->16
- 10.99: derived: exp6b mean 10-15 s GB/s
- 12.6: derived: exp6b first second GB/s
- 0.05: derived: exp7 buffered GB/s, exp3 read cost us, read 256K IOPS k, minutes between exp4 A and B psync16
- 0.00: derived: exp7 IOPS ratio buffered/direct, exp7 latency ratio direct/buffered, exp7 buffered GB/s, exp7 direct QD1 MB/s, exp7 buffered / best real IOPS, directi
- 0.20: derived: exp3 write cost us, exp6b duration s
- 90.6: derived: exp7 IOPS ratio buffered/direct
- 5.4: derived: exp7 buffered GB/s
- 2.4: derived: exp5 knee p99.9/p50
- 0.99: derived: exp4 A psync16 / A peak, exp4 B psync16 / B peak
- 0.8: derived: exp3 harmonic 50/50 k, 4K IOPS GB/s low, write/read ceiling percent (short), read vs Gen5 x4 percent
- 5.0: constant: PCIe generation label
- 5.5: constant: model name
- 6.4: derived: project total TB (final - precondition_before)

## Low-precision matches and unmatched numbers, with context (for hand review)

- 6.2: ...en once sequentially (4 jobs,   blocks,   at 6.2 GB/s) before any read test, s...
- 0.70: ...  random read gave 61.4 µs with direct=1 and 0.70 µs with direct=0 (87 times lo...
- 3.5: ... random write         12,319   50      80.9 (3.5)    69.8 (3.1)    91.6 (3.1) ...
- 3.1: ...        12,319   50      80.9 (3.5)    69.8 (3.1)    91.6 (3.1)    181.2 (46.1...
- 3.1: ...   50      80.9 (3.5)    69.8 (3.1)    91.6 (3.1)    181.2 (46.1)      sequent...
- 0.7: ...   sequential write   19,352   2,536   29.1 (0.7)    28.7 (0.6)    35.1 (1.0) ...
- 0.56: ...e the measured latency (IOPS x latency gives 0.56), so the throughput understat...
- 9.3: ... saturate at 10.6 to 12.9 GB/s and writes at 9.3 to 10.7 GB/s, both far above ...
- 4.6: ....8 (0.6)   98.5 (1.6)   108.4 (2.1)   132.6 (4.6)   197.6 (33.8)   672.1 (432....
- 0.69: ...flawed: page cache)     1,316,919 (79,092)   0.69 (0.05)    1.00 (0.00)     1  ...
- 0.90: ...69 (0.05)    1.00 (0.00)     1               0.90    C: direct=1,   (correct)  ...
- 0.21: ...                 191,798 (504)        83.19 (0.21)   125.10 (0.59)   16        ...
- 0.59: ... 191,798 (504)        83.19 (0.21)   125.10 (0.59)   16              15.96    D...
- 0.69: ...nism. Buffered reads (B) give 1.32 M IOPS at 0.69 µs, 90.6 times the IOPS and 9...
- 9.3: ... 5 GB/s                              Missed (9.3 to 10.7 GB/s)    2     Random...
- 9.4: ...(index 0 to 56)                         mean 9.4                       mean 34...
- 0.68: ...             mean 34.6                      +0.68    Minutes since last write r...
- 6.2: ...10 GB    mean 23.8 (min 0.3)            mean 6.2 (min 0.3)             -0.68  ...
- 0.68: ...)            mean 6.2 (min 0.3)             -0.68    GB written in the 30 min b...
- 0.92: ...             mean 2136.3                    +0.92    Power source at run start ...
- 0.39: ...             on in 42 of 42                 +0.39    Sleep events during the ru...
- 0.68: ...or user activity. Run order correlates (r = +0.68) only through the episode lay...
- 0.92: ...itten in the 30 minutes before the run (r = +0.92: mean 2,136 GB before high ru...

## Derived values (label = value)

- exp7 IOPS ratio buffered/direct = 90.57
- exp7 latency ratio direct/buffered = 99.62
- exp7 buffered GB/s = 5.394
- exp7 direct QD1 MB/s = 59.56
- exp7 buffered / best real IOPS = 5.914
- directio latency ratio = 87.38
- exp4/4b max Little deviation percent, psync = 0.3644
- exp4/4b max Little deviation percent, posixaio = 2.088
- exp4 A psync QD8/QD1 = 7.63
- exp4 A psync QD16/QD1 = 13.14
- exp4 A psync16 / A peak = 98.52
- exp4 B psync16 / B peak = 98.72
- exp4 A psync8 / A peak = 57.23
- exp4 B psync8 / B peak = 60.06
- exp4 A plateau latency ms = 1.351
- exp4 B plateau latency ms = 1.16
- exp4 B vs A peak percent = 17.25
- exp4 B vs A peak percent (222/189) = 17.46
- exp2 16x256KiB latency us = 325.8
- exp2 16x1MiB latency ms = 1.311
- exp2 4K seq-vs-rand percent = 8.952
- exp3 arithmetic blend 50/50 k = 134.9
- exp3 harmonic 50/50 k = 80.73
- exp3 harmonic 70/30 k = 108.1
- exp3 read cost us = 4.538
- exp3 write cost us = 20.24
- exp3 read mean ratio 50/50 = 2.471
- exp3 read p99 ratio 50/50 = 12.35
- exp3 writers in flight 50/50 = 8.713
- exp6a read range diff percent = 0.2614
- exp6a write range diff percent = 1.754
- exp1 randread p99/p50 = 1.161
- exp1 randwrite p99/p50 = 2.597
- exp5 mid p99/p50 = 1.433
- exp5 mid p99.9/p50 = 2.202
- exp5 mid samples above p99.9 = 3347
- exp5 mid samples above p99.99 = 334.7
- exp5 knee p99/p50 = 1.602
- exp5 knee p99.9/p50 = 2.388
- exp5 knee samples above p99.9 = 1.128e+04
- exp5 knee samples above p99.99 = 1128
- exp5 p50 rise percent QD4->16 = 18
- exp5 p99 rise percent QD4->16 = 31.92
- exp5 max ms (QD4, QD16) = 12.98
- exp5 max ms QD16 = 6.133
- fio cores used (exp4 A psync16) = 2.208
- 4K IOPS GB/s low = 0.776
- 4K IOPS GB/s high = 0.912
- 4K IOPS percent of best read bw low = 6.028
- 4K IOPS percent of best read bw high = 7.085
- read 256K IOPS k = 49.1
- write/read ceiling percent (short) = 82.26
- write/read ceiling percent (sustained 11.05) = 86.28
- read vs Gen5 x4 percent = 81.73
- exp6b first second GB/s = 12.64
- exp6b mean 10-15 s GB/s = 10.99
- exp6b mean 5-15 s GB/s = 11.14
- exp6b burst percent = 13.09
- exp6b duration s = 198
- exp6b 300s at measured rate TB = 3.332
- minutes between exp4 A and B psync16 = 53.85
- minutes from exp2 rerun write end to exp4 psync16 run = 11.58
- stage exp12 first pass TB = 1.325
- stage exp12 rerun TB = 1.535
- stage exp34 TB = 0.1478
- stage exp67 TB = 2.311
- project total TB (final - precondition_before) = 6.442
- clean run_all total TB = 4.027
