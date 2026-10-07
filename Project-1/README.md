# Project 1: SIMD advantage profiling (ECSE 4320/6320)

Single-threaded scalar vs NEON SIMD study on an Apple M5 Max: SAXPY, multiply, dot product, 3-point stencil (f32, f64, u32), strided and gather access, alignment and tail effects, roofline, negative cases, and a deliberately naive benchmark. The write-up is `report/REPORT.md`; hypotheses written before the data are in `docs/HYPOTHESES.md`; AI use is in `docs/AI_USE.md`.

## Quick start
Requirements: macOS on Apple Silicon, Apple clang, Python 3 with numpy and matplotlib (no other packages). Nothing is installed system-wide. For measuring: AC power, Low Power Mode off, no heavy background apps.

```
scripts/run_all.sh                    # build, test, vectorization reports, regenerate all plots from committed raw data (about 1 min)
COLLECT=quick scripts/run_all.sh      # also re-measure a reduced version of every experiment into new CSVs (about 20 min)
COLLECT=full  scripts/run_all.sh      # full re-measurement (about 1 hour); needs 8 GB free for the 2 GiB working sets
scripts/run_tests.sh                  # correctness tests only (run before every benchmark)
```

Individual stages: `scripts/build.sh`, `scripts/exp_sweep.sh` (Exp 1, 2, 5), `scripts/exp_align_stride.sh` (Exp 3, 4), `scripts/exp_roofline.sh` (Exp 6, 7), `scripts/exp_extra.sh` (Exp 9 to 13: pointer chase, traffic accounting, dot decomposition, relative misalignment, stride-jump probes), `scripts/make_plots.sh [SWEEP_SID ALIGN_SID ROOF_SID EXTRA_SID]`, `scripts/vecreport.py`, `scripts/session_start.sh <sid>` (environment, timer, clock), `scripts/make_report_pdf.py` (PDF from `report/REPORT.md`; needs `pip install markdown` and Google Chrome). Harness: `bin/bench run|chase|freq|fmapeak|timer|list`.

## Layout
- `src/` kernel template (`kernel_tpl.c`, one translation unit per kernel x dtype x build), harness (`bench.c`), accuracy tool, `naive/` flawed benchmark kept on purpose
- `tests/` correctness tests against a double-double reference
- `scripts/` build, experiment, analysis and plotting scripts; `scripts/config.sh` holds the exact flags per build
- `data/raw/` one CSV per run (timestamp, session, build, kernel, dtype, N, offset, stride, rep, time, thermal state, ...); `data/processed/` tables
- `plots/` PNG and PDF; `vecreports/` compiler remarks, loop bodies and `VECTORIZATION.md`
- `docs/` ENVIRONMENT, METHODOLOGY, HYPOTHESES, PLAN, AI_USE, per-experiment notes, REPRODUCTION
- `report/REPORT.md`

## Optional commands that need sudo (not run by anything here)
```
sudo powermetrics --samplers cpu_power -i 1000 -n 5      # per-cluster frequency while a benchmark runs in another terminal
```
