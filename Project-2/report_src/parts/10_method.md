# 1. Method and environment

## 1.1 Approach

All measurements come from one C program (`membench`) with sub-commands for pointer chasing, streaming kernels, a loaded-latency harness and the TLB and kernel tests. A Python driver runs each experiment in rounds. Within a round every configuration runs once in shuffled order with a fresh random seed, so slow drift cannot align with a sweep axis and each round builds new random permutations. Results are medians over rounds with the minimum and maximum shown. With fewer than 10 rounds an interquartile range is not meaningful, so figures show min to max bands and, for the headline curves, every round as a dot. The number of rounds (n) is listed in every table.

Hypotheses were written before the benchmarks existed and are reproduced in Appendix C. Every later amendment is listed in Appendix D. No benchmark was tuned to match a hypothesis; where a result looked wrong, the benchmark was inspected and, if it was at fault, corrected and the correction recorded (Section 13).

Latency uses a single random cycle through all lines of a footprint (a random permutation closed into one cycle), so every load depends on the previous one and no prefetcher can guess the next address. Streaming bandwidth uses NEON loads and stores with several independent accumulators so that the kernel is limited by memory, not by a dependency chain. All results are consumed (summed into a value that is returned and stored in a global sink) so that the optimizer cannot delete the work (Section 9 shows what happens otherwise).

## 1.2 Environment

| Item | Value |
|---|---|
| Machine | MacBook Pro `Mac17,6`, Apple M5 Max, 36 GB unified memory |
| GPU cores and peak memory bandwidth | 32-core GPU (`system_profiler`). Apple's technical specifications list 460 GB/s for the M5 Max with 18-core CPU and 32-core GPU, and 614 GB/s for the 40-core-GPU part. This machine's 36 GB configuration is offered only with the 32-core GPU, so 460 GB/s is the reference used for every percentage. |
| Cores | 18 = 6 Super (perflevel0) + 12 Performance (perflevel1); no efficiency cores, no SMT |
| L1D | 128 KiB per Super core, 64 KiB per Performance core (`hw.perflevel*.l1dcachesize`) |
| L2 | 16 MiB shared by the 6 Super cores, 8 MiB per cluster of 6 Performance cores (`hw.perflevel*.l2cachesize`, `cpusperl2`) |
| System-level cache | size not exposed by `sysctl`; inferred only from timing |
| Page size, line size | 16 KiB (`hw.pagesize`), 128 B (`hw.cachelinesize`) |
| OS, compiler | macOS 26.5.2 (build 25F84, Darwin 25.5.0); Apple clang 21.0.0 (clang-2100.1.1.101) |
| Compiler flags | `-O2 -std=gnu17 -mcpu=native -ffp-contract=off -Wall -Wextra -Wno-unused-function -pthread` |
| Threads and QoS | each worker sets `QOS_CLASS_USER_INTERACTIVE` on itself; the main thread sets it before any work. No pinning exists on macOS. Placement is checked from cache signatures (Section 1.5) |
| Frequency | automatic (no governor); estimated 4.58 GHz effective on a Super core by a dependent-add calibration after a 300 ms warm-up spin at process start (Section 1.4) |
| Power and thermal | main collection on battery power (about 42% charge, Low Power Mode off, `powermode 0`), no thermal or performance warning recorded at the start of any round or at the end. An earlier collection under AC power gave the same latencies within 1% (L1 0.66 ns in both; DRAM 109.0 and 108.8 ns), so battery operation did not change the result. |
| Background load | recorded per group (`ps`, load average); background daemons (indexing, policy checks) used a few percent of one core at times. Shuffled rounds and medians limit their effect; the maximum values in the tables include such rounds |
| Rounds per experiment | Exp 1: 12; Exp 2 stride and pattern: 5 and 9; stride aliasing tests: 9 and 7; Exp 3: 9 (single-thread) and 6 (loaded); Exp 4: 12; read-ceiling tests: 7; plateau tests: 9; Exp 5 bandwidth: 9; Exp 6: 5 and 7; Exp 7: 12; Exp 8: 5 |
| Timer | `mach_absolute_time`, 24 MHz (41.7 ns tick); every timed region lasts at least 25 ms |

: Table 2. Environment and run protocol. Machine metadata (hardware, OS, compiler and flags, QoS, rounds, warm-up, thermal state, frequency) is also saved in machine-readable form next to every raw data file.

## 1.3 Deviations from the assignment

Intel MLC, `perf` counters, thread pinning, a governor, SMT control and huge pages do not exist or are not accessible on this platform; the SLC size is not exposed and cycle values are estimates. The substitutes and their consequences are listed in Appendix B, Table 3. In short: own benchmarks replace MLC; timing inference replaces counters ({{counters_deviation()}}); QoS classes replace pinning; page locality replaces the huge-page comparison; the SLC appears as a latency ramp.

## 1.4 Frequency and warm-up

A fresh process starts at a low clock and ramps to its steady value over about 100 ms (Section 9, Table 12). Every process therefore spins for 300 ms before any measurement, and each timed region is at least 25 ms. The effective frequency is estimated from a chain of 32 dependent 64-bit adds per iteration, assuming one cycle per add: {{F|.2f}} GHz at the start and end of the collection (4.575 and 4.578 GHz). The assumption is not verified. {{powermetrics_text()}}

## 1.5 Validation

The self-test passes (32 checks): chase cycles visit every node once; the NEON, strided, random-pattern, store and arithmetic kernels match scalar references; the clock and the frequency estimate are within bounds. The checks on the data pass with no flags: latency is non-decreasing with footprint (5% tolerance); L1 latency is 3.0 cycles (inside 2.5 to 6.5); repeatability (interquartile range over median) is 0.4% at 32 KiB, 0.4% at 4 MiB and 1.6% at 1 GiB; no DRAM-resident bandwidth exceeds 460 GB/s (higher values occur only for cache-resident buffers, Section 9); the chase sweep (108.7 ns) and the loaded-harness idle probe ({{v['idle']|.1f}} ns) agree within 4%; one-core N_eff never exceeds the number of chains. A thread with the user-interactive QoS class shows the Super-core signature (96 KiB resident in L1, 12 MiB in L2: 0.66 ns and {{g('e0_placement','ns_per_load',variant='interactive',ws_bytes=12582912)|.1f}} ns), a background-QoS thread a Performance-core signature (96 KiB: {{g('e0_placement','ns_per_load',variant='background',ws_bytes=98304)|.1f}} ns). For more than 6 threads the placement of the extra threads cannot be observed.
