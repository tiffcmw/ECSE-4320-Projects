# Environment and measurability

Captured 2026-10-13 before any benchmark was written. Commands: `sysctl`, `clang --version`, `system_profiler`, `pmset`, `xcrun xctrace`. Per-run metadata is additionally written by `scripts/meta.py` into `data/raw/meta_*.json`.

## Hardware and OS

| Item | Value |
|---|---|
| Machine | MacBook Pro `Mac17,6`, Apple M5 Max, 32-core GPU configuration |
| CPU cores | 18 = 6 "Super" (perflevel0) + 12 "Performance" (perflevel1). No efficiency cores, no SMT. |
| Memory | 36 GB unified LPDDR (`hw.memsize` 38654705664) |
| Page size | 16 KB (`hw.pagesize`) |
| Cache line | 128 B (`hw.cachelinesize`) |
| L1D (Super / Performance) | 128 KB / 64 KB (`hw.perflevel{0,1}.l1dcachesize`) |
| L1I (Super / Performance) | 192 KB / 128 KB |
| L2 (Super / Performance) | 16 MB / 8 MB, shared by 6 cores per cluster (`hw.perflevel*.l2cachesize`, `cpusperl2`) |
| L3 / SLC | Not exposed by sysctl (`hw.l3cachesize` absent; `hw.cachesize[0]` = 3307847680 is not a cache size). SLC capacity must be inferred from timing. |
| Timer | `mach_absolute_time`, 24 MHz tick (41.7 ns), so every timed region is at least 10 ms |
| OS | macOS 26.5.2 (build 25F84), Darwin 25.5.0 |
| Compiler | Apple clang 21.0.0 (clang-2100.1.1.101), target arm64-apple-darwin25.5.0 |
| Python | 3.13.15, numpy 2.5.2, matplotlib 3.11.1 (pandas not used) |

Note: the default `hw.l1dcachesize`/`hw.l2cachesize` (65536, 8388608) describe the Performance tier, not the Super tier.

Published peak DRAM bandwidth: Apple lists 460 GB/s for the 32-core-GPU M5 Max and 614 GB/s for the 40-core-GPU part (secondary sources: Wikipedia "Apple M5", Cloudspress spec table; one review contradicts this). This machine reports 32 GPU cores, so **460 GB/s is the ceiling used for the sanity check**; 614 GB/s is shown as an upper bound if the 460 figure is wrong. Unverified against an Apple primary document.

## What is and is not measurable

| Capability | Status | Substitute used |
|---|---|---|
| Intel MLC | Not available (x86 only) | Own C benchmarks: pointer chase (latency), streaming kernels (bandwidth), loaded-latency harness |
| `perf`, PMU cache/TLB miss counters | Not available. `kpc`/`kperf` needs root (sudo requires a password here; not used). Instruments "CPU Counters" runs via `xctrace` without sudo, but its guided mode exports only cycles and pipeline-bottleneck fractions (useful, delivery, processing, discarded), not L1/L2/TLB miss counts. | Miss behavior is inferred from timing signatures (latency steps vs working set, stride, pages touched). Bottleneck fractions are reported only as supplementary evidence if collected, labeled as such. No counter value is invented. |
| Thread pinning, `taskset` | Not available | QoS `USER_INTERACTIVE` set inside each worker thread (biases to Super cores). Placement verified by the L1D-capacity signature of the latency curve (Super 128 KB vs Performance 64 KB) and optionally by `xctrace` core-type tables. Best effort only. |
| CPU governor, SMT control | Not available | DVFS is automatic. Warmup, repeated trials, effective-frequency estimate from a dependent add chain, thermal state from `pmset -g therm`. |
| `powermetrics` | Needs sudo (password prompt); not run | Frequency estimate by calibration loop; thermal state from `pmset`. |
| Huge pages | Not user-controllable on macOS | Comparison **not possible**. Page locality varied instead (pages touched, stride vs 16 KB page, footprint vs estimated TLB reach). |
| NUMA | None (unified memory) | Not applicable. |
| Power/battery | AC power, Low Power Mode off (`pmset -g`, `powermode 0`) | Recorded per run. |

## Run protocol

AC power, Low Power Mode off, Parallels and torrent clients closed, no heavy foreground apps. Every collection run is wrapped in `caffeinate -dimsu`, begins and ends with `pmset -g therm` and a frequency calibration, uses a warmup that is excluded from statistics, and writes a metadata JSON next to the raw CSV.
