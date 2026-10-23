# Project 1: SIMD advantage profiling on an Apple M5 Max (ECSE 4320/6320)

## 1. Overview

This project measures how much single-thread NEON vectorization improves SAXPY, multiply, dot product and a 3-point stencil (f32, f64, u32), and why the gain changes with the scalar baseline, working set (4 KiB to 2 GiB) and access pattern. It adds a pointer-chase latency probe, alignment, tail, stride and gather tests, a roofline, compiler output (remarks and assembly), and a deliberately naive benchmark that shows how benchmarks go wrong. Each experiment has a hypothesis written before the data (`docs/HYPOTHESES.md`).

## 2. Report

[report/Project1_Report.pdf](report/Project1_Report.pdf) (27 pages). Read it first. Appendix A is the AI-use note, Appendix B is the data and code guide with the evidence index (Table 13).

## 3. Repo layout

```
Project-1/
  README.md
  report/            only the final report PDF (and .gitignore); older drafts are untracked
  report_src/        REPORT.md, the earlier markdown draft; scripts/make_report_pdf.py builds a draft PDF from it
  src/               kernel template (kernel_tpl.c), harness (bench.c), accuracy tool, naive/ (flawed benchmark kept on purpose)
  tests/             correctness suites (test_kernels.c, test_extra.c) against a double-double reference
  scripts/           build, experiment, analysis and plotting scripts; config.sh holds the flags of every build
  data/raw/          one CSV per run, plus powermetrics samples
  data/processed/    derived tables
  plots/             figures (PNG and PDF)
  vecreports/        compiler remarks (remarks/), assembly (asm/), VECTORIZATION.md, summary.md
  docs/              ENVIRONMENT, METHODOLOGY, HYPOTHESES, PLAN, AI_USE, REPRODUCTION, per-experiment notes
  bin/, build/       build output (git-ignored)
```

## 4. Requirements

- Apple Silicon Mac, macOS 26.5.2 was used. Apple clang 21.0.0, C11.
- Python 3.13 with numpy and matplotlib (numpy 2.5.2 and matplotlib 3.11.1 were used). No other packages.
- Only for the optional draft PDF (`scripts/make_report_pdf.py`): `pip install markdown` and Google Chrome.
- Memory: 8 GB free for the 2 GiB working sets in a full re-measurement.

## 5. Build and run

Run everything from `Project-1/`. No sudo is needed by anything here. For measuring, use AC power, Low Power Mode off, and no heavy background load; the plot-only run does not need a quiet machine.

```
scripts/run_tests.sh                  # build and run the correctness suites (about 1 minute)
scripts/run_all.sh                    # build, test, vectorization reports, all plots from the stored raw data (about 1 minute)
COLLECT=quick scripts/run_all.sh      # also re-measure a reduced version of every experiment (about 2 minutes)
COLLECT=full  scripts/run_all.sh      # full re-measurement (about 1 hour)
```

Quick mode writes new CSVs into `data/raw/` and re-plots from them; run it in a scratch clone if you want to keep the committed data and plots untouched. Individual stages: `scripts/build.sh`, `scripts/exp_sweep.sh`, `scripts/exp_align_stride.sh`, `scripts/exp_roofline.sh`, `scripts/exp_extra.sh`, `scripts/make_plots.sh`, `scripts/vecreport.py`, `scripts/session_start.sh <sid>`. The harness is `bin/bench run|chase|freq|fmapeak|timer|list`.

Optional, needs sudo and is not run by anything: `sudo powermetrics --samplers cpu_power -i 1000 -n 5` (per-cluster frequency while a benchmark runs in another terminal).

## 6. Report-to-file map

Plots are in `plots/` (`.png` and `.pdf`), processed tables in `data/processed/`, raw CSVs in `data/raw/`. Session labels in file names: A `phase3`, B `phase4`, C `phase5`, D `ext1`. Collection scripts: `exp_sweep.sh` (sweeps), `exp_align_stride.sh` (alignment, tails, stride), `exp_roofline.sh` (peaks, triad, accuracy, aliasing, naive), `exp_extra.sh` (chase, traffic, dot decomposition, misalignment, stride jump). Plot scripts: `plot_sweep.py`, `plot_align_stride.py`, `plot_roofline.py`, `plot_extra.py`.

| Report item | Plot | Processed table | Raw data |
|---|---|---|---|
| Table 1 (platform, settings), Table 2 (builds) | none | `docs/ENVIRONMENT.md` | `scripts/config.sh`, `data/raw/freq_phase3.csv`, `freq_ext1.csv` |
| Table 3 (what the compiler did) | none | `vecreports/summary.md` | `vecreports/remarks/`, `vecreports/asm/` |
| Tables 4, 5; Figures 1, 2, 3 | `exp1_sweep_f32`, `exp1_sweep_f64`, `exp5_dtype` | `exp1_key_table_phase3.csv` | `sweep_phase3_A..D.csv` |
| Figure 4 | `exp2_saxpy_locality` | `exp1_speedup_phase3.csv` | `sweep_phase3_D.csv` |
| Table 6; Figure 5 | `exp9_chase_latency` | `extra_chase_ext1.csv`, `extra_chasepage_ext1.csv` | `chase_ext1.csv`, `chasepage_ext1.csv` |
| Table 7; Figure 6 | `exp11_dot_decomposition` | `extra_dot_decomposition_ext1.csv` | `dotdec_ext1.csv` |
| Table 8; Figure 7 | `exp12_relative_misalignment`, `exp3_alignment` | `extra_misalign_ext1.csv`, `phase4_summary_phase4.txt` | `misalign_ext1.csv`, `align_phase4.csv` |
| Figure 8 | `exp3_tail_small_n`, `exp3_tail_mod16` | `phase4_summary_phase4.txt` | `tail_phase4.csv` |
| Table 9; Figures 9, 10 | `exp4_stride_gather`, `exp13_stride_jump` | `phase4_summary_phase4.txt`, `extra_summary_ext1.txt` | `stride_phase4.csv`, `stridejump_ext1.csv` |
| Table 10; Figure 11 | `exp10_traffic_accounting` | `extra_traffic_ext1.csv` | `ceiling_ext1.csv` |
| Table 11; Figures 12, 13 | `exp6_peaks`, `exp6_roofline` | `roofline_points_phase5.csv`, `phase5_summary_phase5.txt` | `fmapeak_phase5.csv`, `triad_phase5.csv`, `triadmp_phase5_*.csv` |
| Figure 14 | `exp7_reduction_accuracy` | `phase5_summary_phase5.txt` | `accuracy_phase5.csv` |
| Figure 15 | `exp7_alias_restrict` | `phase5_summary_phase5.txt` | `alias_phase5*.csv`, `restrict_smalln_phase5.csv` |
| Figure 16 | `exp8_naive_vs_fixed` | `phase5_summary_phase5.txt` | `naive_phase5.csv`, `naive_phase5_run1_fix_still_hoisted.csv` |
| Table 12 (expectations against outcomes) | none | `docs/HYPOTHESES.md` | none |
| Table 13 (evidence index) | none | this map, in more detail | none |
| Clock and placement checks | none | `extra_summary_ext1.txt` | `freq_phase3.csv`, `freq_ext1.csv`, `powermetrics_*_20261006.txt` |

## 7. Deviations from the handout

- No hardware counters: `perf` does not exist on macOS and the system profiler's counter recording was not usable; speedups are explained from timing, compiler remarks and assembly (Report, Section 2, Counters).
- No core pinning: the thread migrates among the six Super cores; QoS and repeated rounds are used instead (Report, Section 7).
- The clock is estimated from dependent-add and multiply chains and cross-checked with power sampling, not read from a counter (Report, Section 2, Table 1 and Appendix A).

## 8. Results at a glance

- f32 SAXPY: 5.2x faster than the default scalar build, 2.1x faster than an unrolled scalar loop, 1.35x in DRAM.
- SAXPY bandwidth stays at 147 to 154 GiB/s from 256 KiB to 1 GiB while load latency rises from 0.7 to 111 ns.
- Fast-math dot product: 13.6x faster than the strict loop in the sweep and 14.0x in the decomposition run; 8.4x of the 14.0x comes from independent accumulators and 1.7x from SIMD.
- Offsetting y alone by 4 B slows SAXPY by 26%.

## 9. Correctness and validation

`scripts/run_tests.sh` builds every kernel and runs 80,562 checks (75,018 in `tests/test_kernels.c` plus 5,544 in `tests/test_extra.c`) against a double-double reference, with 0 failures. `scripts/run_all.sh` runs it first. Dot-product error is plotted in Figure 14. Re-running `scripts/run_all.sh` on a fresh clone regenerated every processed table byte for byte from the stored raw data (`docs/REPRODUCTION.md`), and the quick re-measurement agreed with the full run (Report, Appendix B).

## 10. Team and AI use

Authorship, the AI tool used (Claude Code) and the errors found and corrected are in Appendix A of the report. Repository notes: `docs/AI_USE.md`.
