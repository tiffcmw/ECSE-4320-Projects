# Plan

Single-threaded SIMD advantage study on Apple M5 Max (NEON). Everything lives in `Project-1/`. Project-A1 is not touched.

## Phases and commits
| Phase | Content | Exit criterion |
|-------|---------|----------------|
| 0 | ENVIRONMENT.md, HYPOTHESES.md, PLAN.md | committed before any timing |
| 1 | harness (QoS, timer, thermal sampling, checksum sink), 4 kernels x dtypes in separate TUs, builds, tests, timer overhead, frequency estimate, placement check, xctrace counter probe | `scripts/run_tests.sh` green |
| 2 | `-Rpass` remarks and disassembly excerpts per kernel x build | `vecreports/` filled and annotated |
| 3 | Exp 1 (scalar vs auto sweep, all kernels), Exp 2 (SAXPY locality), Exp 5 (dtype) | raw CSV, plots |
| 4 | Exp 3 (alignment, tail), Exp 4 (stride, gather) | raw CSV, plots |
| 5 | Exp 6 (STREAM triad, FMA peak, roofline), Exp 7 (negative cases), Exp 8 (naive-benchmark incident, both datasets kept) | roofline plot |
| 6 | REPORT.md, README.md, AI_USE.md, clean-clone `run_all.sh` check | rubric self-check |

## Design decisions
- Language: C (C11) kernels, one translation unit per kernel and dtype, compiled per build variant to separate object files. Harness is a C driver that calls kernels through function pointers (no cross-TU inlining; LTO off).
- Builds: `scalar` (-O3 -fno-vectorize -fno-slp-vectorize), `scalar_nounroll` (adds -fno-unroll-loops), `auto` (-O3), `native` (-O3 -mcpu=native), `fastmath` (-O3 -ffast-math, reductions only, plus used for negative case A). `-ffp-contract=on` is the clang default and will be stated explicitly in the flags; the primary correctness tolerance is <= 1 ulp for element-wise kernels. Primary scalar baseline will be chosen after comparing `scalar` and `scalar_nounroll` (decision recorded in METHODOLOGY.md).
- Timing: `clock_gettime_nsec_np(CLOCK_UPTIME_RAW)`, inner repeat count auto-calibrated for >= 1 ms per sample, 15+ repetitions per point, warmup discarded, order of configurations randomized with a fixed seed, thermal state sampled before and after each run (`pmset -g therm` plus `sysctl`), throttled runs flagged.
- Threading: harness thread uses `pthread_set_qos_class_np(QOS_CLASS_USER_INTERACTIVE)`. Placement checked by the dependent FMA chain: consistent cycles per FMA across repetitions and no bimodality. Since this chip has two tiers (Super and Performance), the check must distinguish them.
- Frequency: dependent integer add chain, per session, with stated spread. powermetrics requires sudo; it is not run. Commands will be listed for the user in the final summary (ASK before use).
- Counters: xctrace CPU Counters probed once in Phase 1 with bounded effort. If unusable, the report says so and no counter data is shown.
- Working sets: log-spaced 4 KiB to 2 GiB with extra points at 0.5x, 1x, 2x of 64 KiB, 128 KiB, 8 MiB, 16 MiB and a dense region 24 MiB to 512 MiB to locate the SLC (size unknown). All arrays sized as sums of operand footprints (SAXPY has two arrays).
- Data: fixed seed, values in [0.5, 1.5], y re-initialized each repetition for in-place kernels.
- Analysis: numpy and csv only (no pandas). Plots with matplotlib, PNG and PDF, median with IQR error bars.
- Not installing anything system-wide.

## Items needing the user (ASK list)
1. powermetrics (sudo): will be listed, not run.
2. SME streaming mode: judged non-trivial, skipped (no question needed unless the user wants it).
3. Optional x86 Phase 5b: only if a host is provided.
