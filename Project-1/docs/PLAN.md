# Plan

Single-threaded SIMD advantage study on Apple M5 Max (NEON). Everything lives in `Project-1/`; `Project-A1/` is not touched. Hypotheses were committed before the data they predict (`docs/HYPOTHESES.md`).

## Experiments
| Experiment | Content | Script |
|---|---|---|
| Vectorization verification | `-Rpass` remarks and disassembly per kernel and build | `scripts/vecreport.py` |
| Exp 1, 2, 5 | scalar vs auto across working sets for all kernels, SAXPY locality sweep, data types | `scripts/exp_sweep.sh` |
| Exp 3 | alignment (equal offsets), tail | `scripts/exp_align_stride.sh` |
| Exp 4 | stride and gather | `scripts/exp_align_stride.sh` |
| Exp 6 | STREAM-style triad, FMA peak, roofline | `scripts/exp_roofline.sh` |
| Exp 7, 8 | negative cases (reduction, aliasing), naive-benchmark incident with both datasets kept | `scripts/exp_roofline.sh`, `src/naive/` |
| Exp 9 | pointer-chase latency sweep and page-granular chase | `scripts/exp_extra.sh` |
| Exp 10 | memory-traffic accounting (read, incr, copy, scale, add, triad, SAXPY in place and out of place) | `scripts/exp_extra.sh` |
| Exp 11 | dot-product decomposition (1, 4, 8, 16 scalar accumulators) | `scripts/exp_extra.sh` |
| Exp 12, 13 | relative misalignment of x and y, stride-jump probes | `scripts/exp_extra.sh` |

## Design decisions
- Language: C (C11) kernels, one translation unit per kernel, data type and build, compiled to separate object files. The harness is a C driver that calls kernels through function pointers (no cross-unit inlining; LTO off).
- Builds: `scalar` (-O3 -fno-vectorize -fno-slp-vectorize), `scalar_nounroll`, `scalar_unroll8` (primary scalar baseline), `auto` (-O3), `native` (-O3 -mcpu=native), `fastmath` (-O3 -ffast-math, reductions and the negative case). `-ffp-contract=on` is stated explicitly; correctness tolerance is at most 1 ulp for element-wise kernels. The baseline choice is recorded in METHODOLOGY.md.
- Timing: `clock_gettime_nsec_np(CLOCK_UPTIME_RAW)`, inner repeat count calibrated for at least 1 ms per sample, 15 samples per point, one untimed warm call, configuration order shuffled with a fixed seed, thermal pressure sampled before and after each sample.
- Threading: the harness thread uses QoS user-interactive. Placement is checked with a dependent add chain (single mode, no bimodality) and with powermetrics samples.
- Frequency: dependent integer add chain per session; powermetrics (needs sudo) was run by the student.
- Counters: `xctrace` CPU Counters were probed once with bounded effort; the data were not usable and no counter data are shown.
- Working sets: log-spaced 4 KiB to 2 GiB with a denser region from 8 MiB to 1 GiB; all arrays counted in the footprint.
- Data: fixed seed, values in [0.5, 1.5), in-place operands re-initialized before every sample.
- Analysis: numpy and csv only. Plots with matplotlib, PNG and PDF, median with IQR error bars.
- Nothing is installed system-wide. The report PDF needs `pip install markdown` and Google Chrome (`scripts/make_report_pdf.py`).

## Items that need the user
1. powermetrics (sudo): run by the student.
2. SME streaming mode: judged non-trivial and skipped.
3. x86 comparison: only if a host is provided (none was).
