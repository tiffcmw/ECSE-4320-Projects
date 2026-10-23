---
title: "Cache and Memory Performance Profiling on an Apple M5 Max"
subtitle: "ECSE 4320/6320 Class-wide Project 2"
author: "Tiffany Cheng, Marie Morales, Alex Redd"
date: "October 2026"
---

The benchmark code is in the Project-2 folder of the submitted repository. Appendix A lists the source files. Nothing needs to be run to check the report: every figure, table and number below is embedded in this document.

# Summary

This project measures latency, bandwidth, concurrency, cache behavior and address-translation cost on an Apple M5 Max MacBook Pro (macOS, ARM64, 18 cores, 36 GB unified memory) with C benchmarks written for the purpose. Intel MLC, `perf`, a CPU governor, thread pinning, SMT control and user-selectable huge pages do not exist on this platform. Each was replaced by the closest honest substitute, listed in Section 1.3. Every causal statement is labeled *(measured)*, *(inferred)* from measurements, or *(speculation)*. Statements without a cause are plain measurements.

{{headline_table()}}

: Table 1. Headline results. Cycle values use an estimated 4.58 GHz effective clock (dependent-add calibration, Section 1.4). Percentages use the 460 GB/s peak that Apple specifies for the M5 Max with 32-core GPU, which is this machine's configuration (Section 1.2).

**Three most important findings.**

1. **One core is limited by outstanding misses, the chip by something below the DRAM peak.** One core sustains about {{v['Ncore']|.0f}} outstanding random-line misses ({{v['mlp_plateau']|.1f}} GB/s at {{v['L0']|.0f}} ns), consistent with Little's Law *(measured)*. Streaming reads from all cores saturate at {{v['maxbw']|.0f}} GB/s ({{pk(v['maxbw'])|.0f}}% of peak) with 5 or 6 threads, and more threads only add latency *(measured)*. A read-modify-write mix reaches {{v['rmw16']|.0f}} GB/s ({{pk(v['rmw16'])|.0f}}%) and read plus two non-temporal writer threads moves more total traffic than reads alone, so the read-only plateau is not the DRAM limit. Which internal limit sets it is not established (Section 11).
2. **Benchmark design confounds change the answer by large factors.** The data written by a store kernel matters: plain stores of zero lines run at {{v['mix_r0w10_st_z']|.0f}} GB/s against {{v['mix_r0w10_st_r']|.0f}} GB/s for random data, and `stnp` runs {{v['mix_r0w10_nt']/v['mix_r0w10_nt_r']|.1f}}x faster with uniform lines than with random lines. A write-allocate factor of two therefore cannot be read from these data (Section 4). The in-page placement of the lines changes the TLB result: the apparent penalty at 65536 pages is {{pen('paged',65536)|.0f}} ns with the original placement and {{pen('paged_rand',65536)|.0f}} ns once cache-set conflicts are removed (Section 8).
3. **Prefetching decides what "latency" and "bandwidth" mean.** A sequential chase at 128 B steps measures {{v['seq128']|.1f}} ns per node against {{v['rand128']|.0f}} ns for a random chase, {{v['rand128']/v['seq128']|.0f}}x lower *(measured)*, and the benefit ends between 1 KiB and 2 KiB strides. The scattered kernel costs {{v['k_scat_ratio']|.0f}}x the unit-stride cost per element at a 1.5 GiB footprint but only {{v['k_scat_ratio_small']|.1f}}x at 12 KiB (Sections 3 and 7).

{{counters_summary()}}
