# Validation

Frequency used for cycle conversion: 4.58 GHz (estimate). Flags: 0.

| Result | Check | Detail |
|---|---|---|
| PASS | latency non-decreasing with working set (5% tolerance) | no violations |
| PASS | L1 latency not below 2.5 cycles | min 0.655 ns = 3.0 cycles at 4.58 GHz (estimate) |
| PASS | L1 latency within 2.5 to 6.5 cycles (typical 3 to 5) | 0.658 ns = 3.0 cycles |
| PASS | repeatability L1 plateau 32 KiB (IQR/median <= 5%) | IQR/median = 0.5% over n = 9 |
| PASS | repeatability L2 plateau 4 MiB (IQR/median <= 5%) | IQR/median = 0.4% over n = 9 |
| PASS | repeatability DRAM plateau 1 GiB (IQR/median <= 5%) | IQR/median = 0.4% over n = 9 |
| PASS | no DRAM-resident (>= 256 MiB total) bandwidth above 460 GB/s published peak | none |
| NOTE | cache-resident bandwidth above 460 GB/s (expected, not DRAM) | 2 rows, e.g. [('e8_pitfalls', 'r10w0', 'pitfall_resident_bw', '4 MiB', 1087.0, 4194304.0), ('e8_pitfalls', 'r10w0', 'pitfall_resident_bw', '16 MiB', 1094.0, 16777216.0)] |
| PASS | QoS interactive thread shows Super-core cache signature (96 KiB in L1, 12 MiB in L2) | 96 KiB 0.66 ns vs 48 KiB 0.66 ns; 12 MiB 9.4 ns |
| PASS | background QoS shows a different (Performance) signature | 96 KiB 14.7 ns vs 48 KiB 2.14 ns |
| PASS | single-core N_eff = throughput x L0 / 128 B does not exceed K (+15%) | max N_eff/K = 1.00 |
| PASS | DRAM latency: chase sweep (1 GiB) vs loaded-harness idle probe within 15% | 109.1 ns vs 119.5 ns |
| PASS | no thermal or performance warning recorded at any round start | none |
| PASS | thermal state clean at end | Note: No thermal warning level has been recorded Note: No performance warning le |
| PASS | frequency estimate stable start vs end (within 5%) | 4.57 vs 4.58 GHz |
| NOTE | rows excluded for page faults in the timed region | 0 |
| PASS | correctness self-test (chase cycles, kernels vs scalar reference, store variants) | SELFTEST PASSED |
