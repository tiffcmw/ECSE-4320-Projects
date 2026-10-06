# Methodology

## Kernels (src/kernel_tpl.c)
One translation unit per kernel x dtype x build, instantiated from a single template with `-DKERN -DDT -DBUILD`. Uniform ABI `double fn(size_t n, double a, const void *x, void *y, void *z)`. The harness (src/bench.c, compiled `-O2`, no LTO) calls kernels through a table of function pointers, so nothing can be inlined, hoisted, or folded across the timing loop.

| kernel | operation | flops per element | useful bytes per element (dtype size s) |
|--------|-----------|-------------------|------------------------------------------|
| saxpy | y[i] = a*x[i] + y[i] | 2 | 3s (read x, read y, write y) |
| mul | z[i] = x[i]*y[i] | 1 | 3s |
| dot | s += x[i]*y[i] | 2 | 2s |
| stencil | y[i] = .25 x[i-1] + .5 x[i] + .25 x[i+1], i=1..n-2 | 5 | 2s (read x once, write y; neighbours reused) |

dtypes: f32, f64, u32 (wrap-around integer arithmetic; integer stencil uses weights 1,2,1 without normalisation; u32 saxpy uses a = 3). All pointers are `restrict` in the main variants.

## Builds (scripts/config.sh is the source of truth)
Common: `clang -std=c11` (Apple clang 21.0.0), kernel objects compiled one at a time.

| build | flags | purpose |
|-------|-------|---------|
| scalar | `-O3 -fno-vectorize -fno-slp-vectorize -ffp-contract=on` | assignment-defined scalar baseline (secondary here, see below) |
| scalar_nounroll | `... -fno-unroll-loops` | check whether clang unrolls the scalar loop (it did not differ) |
| scalar_unroll8 | `-O3 -fno-vectorize -fno-slp-vectorize -DFORCE_UNROLL -ffp-contract=on` (pragma `unroll_count(8)`) | best-effort scalar, primary baseline |
| auto | `-O3 -ffp-contract=on` | default auto-vectorization |
| native | `-O3 -mcpu=native -ffp-contract=on` | `native` resolves to `apple-m4` in this clang (checked with `-###`) |
| fastmath | `-O3 -ffast-math -ffp-contract=fast` | separate build, reductions especially |

FMA contraction: `-ffp-contract=on` (contract within a statement) for every non-fast-math build, so `a*x[i] + y[i]` becomes a fused multiply-add in the scalar and the vector builds alike. This is stated because fused and unfused results differ in the last bit; the correctness tolerance accounts for it.

Primary scalar baseline: `scalar_unroll8`. Reason: in the Phase 1 smoke run `scalar` and `scalar_nounroll` were identical and about 1.6x slower than the unrolled loop for SAXPY, meaning the assignment-defined scalar build is limited by loop overhead (about one iteration per cycle) and would inflate the SIMD speedup. Both are plotted.

## Timing
- Clock: `clock_gettime_nsec_np(CLOCK_UPTIME_RAW)`. The tick is 41.67 ns (24 MHz counter; `bench timer` shows nonzero back-to-back deltas of 41 ns). Each sample loops the kernel until it lasts at least 1 ms (inner repeat count calibrated from 5 warm calls), so tick quantization is below 0.005%.
- Call overhead (function pointer + barrier + sink) measured with an empty kernel through the same pointer: about 0.95 ns per call, subtracted and recorded in each CSV row (`ovh_ns`). It matters only for tiny working sets (a 4 KiB SAXPY call is about 170 ns).
- Dead-code prevention: kernel return value summed into an accumulator that is passed to an empty `asm volatile` with a `w` constraint; `asm volatile("" ::: "memory")` after every call; kernels in a different translation unit from the loop.
- Each sample: (1) re-initialise the in-place operand (SAXPY y) with a fixed pattern, (2) one untimed warm call in steady state, (3) timed loop of `inner_reps` calls. Arrays are first-touched during initialisation, outside timing. Values are in [0.5, 1.5) (f32, f64), no denormals; SAXPY uses a = 1e-6 so y stays near 1 over up to millions of calls.
- Data layout: one anonymous mmap slab per configuration visit; arrays are separated by a page-rounded size plus a 2176 B skew so that they do not alias in L1 sets; a byte offset (default 0) shifts every array start.
- Repetitions: samples per point = passes x reps (default 3 x 5 = 15). Each pass visits all configurations in a different order, shuffled with a fixed-seed generator, so thermal drift is spread across configurations.
- Statistics: median, IQR (q1 to q3), min, max over samples. Error bars in plots are IQR. Samples with thermal pressure level >= 1 (sampled before and after each timed loop) would be dropped and counted; none so far.
- Metrics: ns per call, ns per element, GFLOP/s (flops from the table), GiB/s of useful bytes (from the table, not including write-allocate or line-granularity waste), cycles per element = ns per element x effective GHz.

## Core placement (no pinning on macOS)
The harness thread sets QoS `user-interactive` via `pthread_set_qos_class_self_np`. Placement was checked with a dependent add chain (`bench freq`, 200 reps): `data/raw/freq_user-interactive_probe.csv`. Median 0.2182 ns per add, IQR 0.2176 to 0.2195 ns (0.9% spread), single mode, no bimodality. Other QoS classes: user-initiated and utility give the same clock; background runs on a slow cluster (median 0.747 ns per add, about 1.34 GHz, wide spread) (`freq_*_probe.csv`). Which tier: a powermetrics sample run by the student (`data/raw/powermetrics_sample_20261006.txt`) shows three clusters: P0 (CPUs 0 to 5) and P1 (CPUs 6 to 11), whose highest frequency state is 4380 MHz, and S (CPUs 12 to 17), whose highest state is 4608 MHz. The 4.58 GHz measured here is above the highest P state, so the add chain cannot have been running on a Performance core (given the 1-cycle-add assumption), and it is within 0.5% of the S-cluster top state. That identifies the Super tier. Limits of that first sample: it was idle, so it shows the available states, not the placement of a run; the 0.5% gap between 4.587 and 4.608 GHz is unexplained (a timer or loop effect of that size is possible); the 12-process bandwidth run was not matched to clusters.

Placement verified during a benchmark (student-run powermetrics, f32 SAXPY `auto` at a 32 MiB working set): four 1 s samples, `data/raw/powermetrics_during_benchmark_20261006.txt` (powermetrics in a separate terminal) and `data/raw/powermetrics_during_benchmark_combined_20261006.txt` (three consecutive samples from one combined command, benchmark confirmed running). In all four the S cluster was 100% active and every busy S CPU ran at 4608 MHz; the P0 cluster was idle or at background level and P1 showed background activity at about 1.4 GHz; CPU power was 14.6 to 14.8 W (idle samples: 0.2 to 0.6 W). The S-cluster time-averaged frequency was 4548 MHz in the first sample and 4596, 4588, 4596 MHz in the combined run (the cluster spent a small share of time in states from 4236 to 4512 MHz). Two consequences. (1) The thread is not pinned to one core: in every sample the six S cores showed about 31 to 35% (CPU 12) and 10 to 16% (the others), summing to 107 to 116%, which fits one thread migrating among the Super cores (100%) plus 7 to 16 points of other work (powermetrics, caffeinate, the shell). Migration within the cluster keeps the shared L2 but not L1 contents; the small run-to-run noise (median CV 1.8%) suggests it does little harm, but I did not isolate its effect. (2) The clock is close to, but not exactly, constant: averages of 4548 to 4596 MHz bracket my 4.587 GHz estimate (0.9% above the lowest, 0.1 to 0.2% below the other three). Cycles per element are therefore uncertain by about 1%. Only this one benchmark was sampled; other benchmarks were assumed to behave the same (same QoS) but were not sampled.

## Frequency estimate
Dependent chain `add x, x, y` (64 per loop body, loop control off the critical path). Assuming 1 cycle per add: 4.58 GHz (1 / 0.2182 ns). Cross-check with a dependent integer multiply chain: 0.6555 ns = 3.00 cycles at 4.58 GHz, and a dependent scalar fmadd chain: 0.6712 ns = 3.08 cycles. The integer multiply result matching a whole 3 cycles supports the 1-cycle-add assumption. Uncertainty: IQR about +/- 0.5%, plus an unverified assumption that adds are not fused or eliminated (if two adds per cycle were possible the true clock would be 2.3 GHz; the mul and fmadd latencies make that unlikely). Re-measured per session by `scripts/session_start.sh`. powermetrics (needs sudo) was run once by the student after the experiments; it lists S-cluster states up to 4608 MHz, consistent with this estimate (see Core placement). Frequency during the runs was not logged by powermetrics.

## Correctness (tests/test_kernels.c, scripts/run_tests.sh)
Every kernel x dtype x build (90 combinations incl. fast-math) over 29 sizes (0 to 100003, including odd sizes and sizes with remainders mod 4, 8, 16, 32, 64) x 7 start offsets (0, 4, 8, 12, 16, 60, 64 bytes), data from the fixed-seed generator, with 64-element guard regions to catch out-of-bounds writes. Reference: scalar loops with double-double arithmetic compiled with `-ffp-contract=off`. Note: on arm64 macOS `long double` is 64-bit (sizeof = 8), so a long double accumulator gives no extra precision; double-double (about 106 bits) is used instead.
Tolerances: SAXPY and mul <= 1 ulp from the correctly rounded result (observed 0); stencil <= 2 ulp (observed 1, two roundings in the sum); dot relative error <= n * eps(dtype) (loose worst-case bound; observed values printed); u32 exact modulo 2^32. A mutation check (an off-by-one loop bound, a wrong stencil weight) makes the suite fail (191 and 177 failures respectively), so it can detect these faults.

## Counters
`perf` does not exist on macOS. `xctrace record --template "CPU Counters"` works only with `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` (Xcode is installed but not the selected developer directory). The recording succeeded, but the exported `MetricAggregationForThread` table holds only per-thread aggregates of `cycle` and four bottleneck categories (useful, delivery, processing, discarded); the other four were zero in my parse, and the `cycle` totals disagreed with timing-based expectations by about 4.7x for a known workload. No FP-instruction, vector-instruction, or cache-miss events are available. The units and sampling of this table were not validated, so no counter data is used anywhere in this report. kpc needs root and private APIs and was not attempted.

## Controls
AC power, Low Power Mode off (`pmset -g`: powermode 0), `caffeinate -dimsu` around every run, thermal pressure sampled per sample, no other heavy applications (not enforced by the harness; the load average is logged in `docs/ENVIRONMENT_sessions.log`).
