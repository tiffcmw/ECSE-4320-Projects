# Methodology

## Build

`scripts/build.sh` compiles every `src/*.c` with
`clang -O2 -std=c17 -Wall -Wextra -mcpu=native -pthread` (Apple clang 21.0.0). No `-ffast-math`. Benchmarks that must not be vectorized or eliminated rely on loop-carried dependencies and a sink (`asm volatile("" :: "r"(v) : "memory")`), not on lower optimization levels.

## Timing

- One clock everywhere: `mach_absolute_time()` converted to ns (`src/platform.h`, `now_ns`).
- Measured in E0 (`data/raw/noise_*.csv`, 3 invocations): tick granularity 41 ns (the 24 MHz timebase), call overhead 6.6 to 9.0 ns. Overhead is negligible because every timed region is at least 20 ms (chase auto-sizes `steps`, other kernels loop until 20 ms), so timer error is below 0.0003%.
- Fixed-work noise floor (dependent 64-bit multiply-add chain, 20 M iterations, 100 reps): median 17.48 ms, min 17.38 ms, IQR/median 0.5% to 0.6%, 0.874 ns per iteration, stable across the 3 invocations to within 0.1%. Differences smaller than about 1% between configurations are therefore not interpreted.

## Noise control (per run)

- Plugged in (AC), Low Power Mode off, no other heavy applications, whole experiment under `caffeinate -dimsu`.
- `pmset -g therm` and `pmset -g batt` captured before and after every benchmark invocation (`runlib.py`, columns `therm_before`, `therm_after`). A row is flagged `throttled=1` if a speed limit or warning appears, a CPU went unavailable, the machine is on battery or in Low Power Mode, or the before/after strings differ. Flagged rows stay in raw data and are excluded from medians by `analyze.py`.
- Configurations are shuffled every round (seeded RNG, seed recorded in code) so thermal drift does not align with any parameter.
- Each point has at least 10 timed repetitions across several rounds (typically 3 rounds x 5 reps), with 2 warmup repetitions per invocation that are not recorded. Reported: median, IQR, min.

## Validity checks

- Every chase is verified as a single cycle over all nodes before timing (`chase_verify`); the binary aborts otherwise. `tests/test_harness.c` checks this for several sizes and strides, checks that the verifier rejects a two-cycle layout, and checks that n steps returns to the start and n-1 does not (known-answer checksum).
- Timed regions record `getrusage` minor page faults. After initialization the timed region should show 0; nonzero means first-touch cost leaked into the measurement.
- Known-answer ranges: L1-resident dependent load should be a few cycles (about 1 ns or less on this core clock), DRAM latency tens of ns to roughly 100 ns. Results outside these are flagged in the report rather than silently accepted.
- Bandwidth is cross-checked with a second method (STREAM-like triad) added in Phase 2.

## Counters and OS statistics available on this machine

- **Instruments CPU Counters** works without sudo when `xctrace` is invoked with `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` (no system-wide change). The recorded trace contains `CoreTypeByThread` (per-10 ms core type: "Super" or "Performance") and `CounterMetricAggregatedForProcess` (cycles and bottleneck breakdown). This is the evidence used to verify core-tier placement of a QoS class, so placement is **observed**, not guaranteed: it holds only for the sampled runs.
- It is not a raw L1/L2/TLB miss counter interface; the default mode ("CPU Bottlenecks") reports cycles, useful work, instruction-delivery, instruction-processing and discarded bottlenecks. Miss behavior is therefore shown mainly through latency-vs-working-set curves.
- `getrusage` page faults, `vm_stat` and `sysctl` are used where relevant.
- `powermetrics` needs sudo and is only used if the user approves (see `PLAN.md`).

## Limits

No thread pinning (QoS steers, does not pin); no direct L1/L2/TLB miss counters; SLC size not exposed; unified memory means CPU and GPU share DRAM and the OS may use compressed memory; results are for one machine and one OS build (macOS 26.5.2).
