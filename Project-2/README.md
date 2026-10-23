# Project 2: cache and memory performance profiling on an Apple M5 Max (ECSE 4320/6320)

## 1. Overview

This project measures latency, bandwidth, concurrency, cache behavior and address-translation (TLB) cost on an Apple M5 Max MacBook Pro (macOS, ARM64, 18 cores, 36 GB unified memory) with C benchmarks written for the purpose. Seven experiments cover zero-queue latency, access pattern and granularity, read/write mix, an intensity sweep with the knee and Little's Law, the working-set sweep, kernel cost with cache misses, and TLB-miss impact, plus a set of benchmark pitfalls. Hypotheses were written before the benchmarks existed (`hypotheses.md`) and every later amendment is recorded.

## 2. Report

[report/Project2_Report.pdf](report/Project2_Report.pdf) (28 pages). Read it first. Appendix A is the AI-use note, Appendix B the code map and reproduction guide, Appendix C and D the hypotheses and amendments.

## 3. Repo layout

```
Project-2/
  README.md
  hypotheses.md      predictions written before the benchmarks, with every later amendment
  report/            only the final report PDF (and .gitignore); older drafts and build output are untracked
  report_src/        parts/*.md and verdicts.txt: the earlier markdown source that scripts/build_report.py assembles
  src/               membench.c (all kernels and sub-commands), common.h, pmu.h (optional kperf access, needs root)
  scripts/           build, run_exp.py (experiment driver), parse, validate, plot, build_report, check_report, make_docx, run_privileged.sh
  data/raw/          per-round CSVs, logs and metadata JSON, one set per collection session
  data/processed/    medians, min, max, n per configuration (CSV), tables.md, validation.md, selftest.log
  plots/             figures (PNG at 220 dpi and PDF)
  docs/              ENVIRONMENT, PLAN
  bin/               build output (git-ignored)
```

## 4. Requirements

- Apple Silicon Mac, macOS 26.5.2 (Darwin 25.5.0) was used; Xcode command line tools with Apple clang 21.0.0.
- Python 3.13 with numpy and matplotlib (numpy 2.5.2 and matplotlib 3.11.1 were used).
- Only for the earlier markdown-to-Word draft (`scripts/build_report.py`, `scripts/make_docx.py`): pandoc (3.12.1 was used) and LibreOffice at `/Applications/LibreOffice.app`. `run_all.sh` skips these if pandoc is missing.
- Memory: about 6 GB free for a full re-measurement.

## 5. Build and run

Run from `Project-2/`. Nothing needs sudo except the optional counter run. For measuring, use AC power, Low Power Mode off and a quiet machine.

```
scripts/run_all.sh                   # build, self-test, parse, validate, plot from the stored raw data (about 1 minute)
COLLECT=quick scripts/run_all.sh     # first re-measure reduced sweeps (about 4 minutes)
COLLECT=full  scripts/run_all.sh     # first re-measure everything (about 30 minutes, quiet machine, AC power)
sudo scripts/run_privileged.sh       # optional: powermetrics clock check and PMU counters; then rerun scripts/run_all.sh
```

Raw CSVs are never overwritten: every collection writes `data/raw/<group>_<session>.csv`, a log and a metadata JSON. Parsing uses the newest full session (a quick session is newer than the stored full one, so run quick mode in a scratch clone if you want to keep the committed processed data and plots unchanged). Steps of `run_all.sh`: `scripts/build.sh`, `scripts/diagnostics.sh`, `scripts/run_exp.py --profile quick|full --sid ID`, `scripts/parse.py`, `scripts/validate.py`, `scripts/plot.py`.

With pandoc installed, `run_all.sh` also runs `scripts/build_report.py` and `scripts/check_report.py`, then `scripts/make_docx.py`. Their outputs (draft files `ECSE4320_Project2_Report.md`, `.docx`, `.pdf` and `numbers.json`) land in `report/`, where they are git-ignored. The submitted report is `report/Project2_Report.pdf`, not these drafts.

## 6. Report-to-file map

Figures are `plots/<name>.png` and `.pdf`, produced by `scripts/plot.py`. Tables 1 and 4 to 11 are built by the named function in `scripts/build_report.py` from `data/processed/`; the raw files are in `data/raw/<group>_<session>.csv`.

| Report item | Plot or build function | Data (processed `data/processed/<name>.csv`) |
|---|---|---|
| Table 1 (headline results) | `headline_table` | `e1_chase`, `e5_bw`, `e4_loaded`, `e4_mlp`, `e3_mix_bw` |
| Table 2 (environment, run protocol) | `report_src/parts/10_method.md`, `scripts/meta.py` | `SESSION.json`, `data/raw/meta_*.json`, `docs/ENVIRONMENT.md` |
| Table 3 (deviations from the assignment) | `report_src/parts/50_appendices.md` | `docs/ENVIRONMENT.md` |
| Table 4; Figure 1 | `exp1_table`; `exp1_zero_queue` | `e1_chase` |
| Figure 2 | `exp2_pattern_granularity` | `e2_chase_stride`, `e2_pat` |
| Figure 3 | `exp2b_stride_aliasing` | `e2_alias`, `e6_stride` |
| Table 5; Figure 4 | `mix_table`; `exp3_rw_mix` | `e3_mix_bw`, `e3_mix_loaded` |
| Table 6 | `content_table` | `e3_mix_bw` |
| Table 7 (thread sweep); Figure 5 | `knee_table`; `exp4_intensity` | `e4_loaded`, `e4_mlp` |
| Table 8 (injection delay) | `delay_table` | `e4_loaded` |
| Figure 6 | `exp4b_read_ceiling` | `e11_ceiling` |
| Figure 7 | `exp5_working_set` | `e1_chase`, `e5_bw` |
| Figure 8 | `exp5b_plateau_tests` | `e12_plateau` |
| Table 9 (AMAT model); Figure 9 | `amat_table`; `exp6_kernels` | `e6_kern`, `e1_chase`, `e4_mlp` |
| Table 10; Figure 10 | `tlb_table`; `exp7_tlb` | `e7_tlb`, `e0_placement` |
| Figure 11 | `exp8_pitfalls` | `e8_pitfalls`, `e5_bw`, `e1_chase` |
| Table 11 (Little's Law) | `report_src/parts/40_synthesis.md` | `e1_chase`, `e3_*`, `e4_*` |
| Tables 12, 13 (verdicts, amendments) | `hyp_table` | `hypotheses.md`, `report_src/verdicts.txt` |
| Appendix B (dead-code evidence) | none | `data/raw/dce_asm.txt` |
| Appendix E (counter attempts) | `scripts/run_privileged.sh`, `scripts/xctrace_bottleneck.py` | `data/raw/counters/` |

## 7. Deviations from the handout

- No Intel MLC: an own loaded-latency harness with injected delay replaces it (Report, Section 1.3 and Table 3, Section 5).
- No `perf` and no usable hardware counters: cache and TLB behavior is inferred from timing; reading counters through the private kperf frameworks needs sudo, which was not available (Report, Section 1.3, Summary, Appendix E).
- No CPU governor, thread pinning or SMT control: QoS classes, repeated shuffled rounds and a frequency estimate replace them (Report, Sections 1.3 and 1.4).
- No user-selectable huge pages: page locality replaces the huge-page comparison, and the report makes no statement about huge pages (Report, Sections 1.3 and 8).

## 8. Results at a glance

- L1 hit latency 0.66 ns (3.0 cycles est.), L2 7.12 ns at 2 MiB, DRAM 108.7 ns at 1 GiB.
- One core sustains about 19 outstanding random-line misses (21.9 GB/s), consistent with Little's Law.
- Chip streaming read bandwidth saturates at 293 GB/s (64% of the 460 GB/s peak) with 5 or 6 threads; read-modify-write reaches 374 GB/s (81%).
- Plain stores of zero lines run at 277 GB/s against 68 GB/s for random data, so the data written by a store kernel changes the answer.
- A sequential chase at 128 B steps measures 7.8 ns per node against 108 ns for a random chase.

## 9. Correctness and validation

`scripts/run_all.sh` runs `bin/membench selftest` (`data/processed/selftest.log`) and `scripts/validate.py` (`data/processed/validation.md`: sanity checks on every configuration). `scripts/check_report.py` recomputes the report's derived numbers from the raw per-round CSVs and fails on mismatch (50 checks pass). The unused-result read loop is shown to be removed by the compiler with `otool` evidence in Appendix B of the report.

Some raw metadata files in `data/raw/` (`meta_*_full.json`) record the original machine path and were not altered.

## 10. Team and AI use

Team: Tiffany Cheng (Exp 1, 2 and 5), Marie Morales (Exp 3 and 4) and Alex Redd (Exp 6, 7 and 8, and the counter attempts), as stated in Appendix A of the report. Authorship, the AI tool used (Claude Code, model claude-sonnet-5-5) and the problems found and fixed are in Appendix A; benchmark flaws found are in Section 13.
