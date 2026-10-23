# Project 3: SSD performance profiling on an Apple M5 Max (ECSE 4320/6320)

## 1. Overview

This project profiles the internal SSD of an M5 Max MacBook Pro (APPLE SSD AP2048Z, 2 TB, controller inside the SoC) through **one disposable 32 GiB file** inside `scratch.noindex/` on APFS, using fio with direct I/O (`F_NOCACHE`). No raw device is ever touched. Seven experiments cover QD1 baselines, block size, read/write mix, a queue-depth sweep and its knee, tail latency, working-set and device-state effects (including a 2.2 TB sustained write), and misleading setups (page cache, wrong queue depth). Predictions were committed to git history before any experiment data (`HYPOTHESES.md`, commits `4f2fee8` and `69b59d1`) and are scored in the report.

## 2. Report

[report/Project3_Report.pdf](report/Project3_Report.pdf) (14 pages). Read it first. Section 9 is the hypothesis scorecard, Section 10 the anomalies, Section 13 the reproducibility note, Appendix A the AI-use note.

## 3. Repo layout

```
Project-3/
  README.md, HYPOTHESES.md
  report/            only the final report PDF (and .gitignore); older drafts and build output are untracked
  report_src/        REPORT.template.md and REPORT.md: the earlier markdown draft (scripts/build_report.py fills the template)
  fio/               one job file per experiment; header comments list fixed and varied knobs
  scripts/           drivers (run_*.sh), common.sh (safety guards), parse_fio.py, make_tables.py, plots.py, analysis and report builders
  scripts/docx/      make_docx.js, the Word report generator (needs npm install docx)
  data/raw/          untouched fio JSON, one file per run: exp__knob=value__...__tN.json; health/ has before/after snapshots per stage
  data/processed/    all_runs.csv, summary.csv, tables/*.md, docx_number_trace.md
  plots/             PNG and PDF figures; plots/docx/ holds the PNGs used in the Word report
  scratch.noindex/   the 32 GiB test file and fio scratch files (git-ignored, never commit)
```

Key scripts: `scripts/run_00_precondition.sh`, `run_01_directio_check.sh`, `run_02_exp1_exp2.sh`, `run_03_exp3_exp4.sh`, `run_04_exp5_tail.sh`, `run_05_exp6_exp7.sh`, `run_06_drift_series.sh`, `run_07_exp4_replicate.sh`, `run_engine_check.sh`, `run_all.sh`, `wait_for_ac.sh`, `cleanup.sh`.

## 4. Requirements

- Apple Silicon Mac with an internal SSD, macOS 27.0.1 (the experiments ran on 27.0.1; the engine check on 26.5.2 is kept in `data/raw/engine_check_macos26.5.2/`).
- fio 3.43 and smartmontools (smartctl 7.5): `brew install fio smartmontools`.
- Python 3.13 with matplotlib and numpy (matplotlib 3.11.2 and numpy 2.5.4 were used). `run_all.sh` creates `.venv/` with them if it is missing.
- Optional, for the Word report only: node with `cd scripts/docx && npm install docx`, and pandoc for the number trace.
- `libaio` and `io_uring` do not exist on macOS (see section 7).

## 5. Build and run

Run from `Project-3/`. Nothing needs sudo (`smartctl -a disk0` works without it; no privileged command was run). Conditions: **charger plugged in, lid open, machine idle.** The drivers refuse to run on battery or in Low Power Mode, move a run to `data/raw/invalid/` if the Mac left AC power or slept, and hold a `caffeinate -ims` assertion. Free space: the test file is 32 GiB and the guard aborts if less than 20% of the volume would remain. FileVault was on for all measurements, so hardware encryption is part of every number. The SSD wear cost is large (see below).

```
brew install fio smartmontools
bash scripts/run_all.sh        # full study, about 3 hours, about 4 TB of SSD writes
bash scripts/cleanup.sh        # deletes only the test file and marker files
```

`run_all.sh` waits for AC power, then runs the engine check, preconditions the 32 GiB file, runs the direct-I/O check (stops if `direct=1` looks cache-like), Exp 1 to 7, a drift series and the Exp 4 replicate, and rebuilds the tables and figures.

**There is no quick measurement mode.** Two shorter options exist:

- Re-analysis from the stored raw data (a few seconds, no SSD writes, no AC requirement). It regenerated `data/processed/` identically in a clean copy:

```
python3 -m venv .venv && .venv/bin/pip install matplotlib numpy       # once
for s in parse_fio make_tables analyze_state_split check_smart_reads plots build_report; do .venv/bin/python -I scripts/$s.py; done
```

- `SMOKE=1 bash scripts/run_0X_*.sh` runs 3 s versions of one stage into `data/smoke/` (git-ignored). It needs the preconditioned test file from `scripts/run_00_precondition.sh`.

Optional Word report: `.venv/bin/python -I scripts/export_docx_data.py && node scripts/docx/make_docx.js && .venv/bin/python -I scripts/check_docx_numbers.py` writes `report/Project3_SSD_Report.docx` (git-ignored) and `data/processed/docx_number_trace.md`. The submitted report is `report/Project3_Report.pdf`.

SSD write volume, measured by the SMART counter:

| Stage | Host bytes written |
|---|---|
| Precondition fill | 0.034 TB |
| Exp 1+2, first pass (writes later declared invalid, kept as evidence) | 1.325 TB |
| Exp 1+2, repeated write runs | 1.535 TB |
| Exp 3+4 | 0.148 TB |
| Exp 6+7 (2.2 TB cap on the sustained write) | 2.311 TB |
| Everything else (Exp 5, drift runs, replicate) | under 0.01 TB |
| Smoke tests during development (not in any result) | about 0.5 TB |
| **Whole project, from the counter** | **about 6.4 TB (9.59 to 16.03 TB lifetime); wear indicator still 0%** |

## 6. Report-to-file map

Tables are `data/processed/tables/<name>.md`, generated by `scripts/make_tables.py` from `data/processed/summary.csv` (`scripts/parse_fio.py` from `data/raw/`). Figures are `plots/<name>.png` and `.pdf`, produced by `scripts/plots.py`. In the PDF the tables are typeset by `scripts/docx/make_docx.js` from `report/docx_data.json` (written by `scripts/export_docx_data.py`).

| Report item | Table or plot | Raw data (`data/raw/`) | Fio job (`fio/`) |
|---|---|---|---|
| Table 1; Figure 1 (Exp 1) | `tables/exp1.md`; `fig1_baseline_qd1` | `exp1/` | `01_baseline.fio` |
| Table 2; Figure 2 (Exp 2) | `tables/exp2.md`; `fig2_blocksize` | `exp2/` | `02_blocksize.fio` |
| Table 3; Figure 3 (Exp 3) | `tables/exp3.md`; `fig3_rwmix` | `exp3/` | `03_rwmix.fio` |
| Table 4; Figure 4 (Exp 4) | `tables/exp4.md`; `fig4_qd_sweep` | `exp4/`, `exp4b/` | `04_qd_sweep.fio` |
| Table 5; Figure 5 (Exp 5) | `tables/exp5.md`; `fig5_tail_latency` | `exp5/` | `05_tail.fio` |
| Table 6; Figure 6 (Exp 6) | `tables/exp6b.md`, `tables/exp6a.md`; `fig6_working_set_and_sustained_write` | `exp6a/`, `exp6b/` | `06_workingset.fio`, `06_sustained_write.fio` |
| Table 7; Figure 7 (Exp 7) | `tables/exp7.md`; `fig7_misleading_setups` | `exp7/` | `07_misleading.fio` |
| Table 8 (scorecard) | typed in `scripts/docx/make_docx.js` from `HYPOTHESES.md` | none | none |
| Table 9; Figure 8 (two IOPS levels) | `tables/state_split.md` (`scripts/analyze_state_split.py`); `fig8_state_drift` | `drift/`, `driftseries/`, `exp4/`, `exp4b/` | `04_qd_sweep.fio` |
| Table 10; Figure 9 (ceilings) | `D["ceilings"]` in `scripts/export_docx_data.py`; `fig9_roofline_summary` | `data/processed/summary.csv` | none |
| Section 1 (methodology), Section 13 | `data/raw/health/`, `data/raw/precondition/`, `data/raw/engine_check_*/` | as listed | `00_precondition.fio`, `engine_check.fio` |
| Direct against buffered check (Section 1) | `data/raw/directio_check/` | as listed | `00_directio_check.fio` |
| SMART cross-check | `tables/smart_read_check.md` | `data/raw/health/` | none |
| Quarantined runs (Section 10) | none | `invalid_sleep_2026-10-22/` | none |

`data/processed/docx_number_trace.md` traces every number in the Word source of the report to the data.

## 7. Deviations from the handout

- No `libaio` or `io_uring` on macOS (detected by `scripts/run_engine_check.sh`, recorded in `data/raw/engine_check_macos27.0.1/engines.txt`). The fallback is `psync` with `numjobs=N` (effective depth N) and `posixaio` with `iodepth=N`; neither is assumed to give the configured depth, and Little's law is checked for every run (Report, Section 1 and Section 5).
- fio runs at most about 16 jobs at once on this Mac (`kern.sysv.shmall` is 4 MB), so `psync` depths stop at 16. `posixaio` reaches depth 256 on macOS 27.0.1 but was capped at 16 on 26.5.2 (Report, Section 1, Amendment B in Section 9).
- File on APFS under FileVault, not a raw device: controller, encryption, copy-on-write and OS cache layers cannot be disabled, so results are file-on-APFS performance (Report, Section 11).
- Sustained write is a single run capped at 2.2 TB or 300 s to limit wear; it ended at 2.2 TB after 198 s (Report, Section 7, Table 6).
- No privileged tools, no SSD temperature finer than 10 s sampling, no PCIe link state (Report, Section 1).

## 8. Results at a glance

- 4 KiB random read at QD1 takes 55 to 70 µs; reads reach 12.9 GB/s and writes about 10.6 GB/s.
- 4 KiB random reads saturate at 189 k to 223 k IOPS with the knee at QD16; 4 KiB random writes reach only 47 k IOPS.
- A 2.2 TB sustained sequential write held 11.0 GB/s with no cliff (a result limited by the test, not proof that no SLC-style cache exists).
- A page-cache run inflates IOPS 90 times (1.32 M against 14.5 k).
- The same read workload ran at two speed levels (about 189 k and 222 k IOPS); the cause was not established (Report, Section 10).

## 9. Correctness and validation

- `scripts/common.sh` guards: `guard_path` aborts unless the target is inside `scratch.noindex/` (`/dev/*` and symlinks refused); free-space check; `check_power` before every run; a result check after every run that moves invalid runs to `data/raw/invalid/`; health logs (`smartctl`, `pmset`, `df`, top processes, versions) before and after every stage in `data/raw/health/`.
- Direct I/O is verified by behavior: `direct=1` against `direct=0` gives an 87 times latency difference and the check script stops the campaign if `direct=1` looks cache-like; SMART "Data Units Read" is never lower than fio's byte count (`data/processed/tables/smart_read_check.md`); fio write bytes match SMART "Data Units Written" to 0.01%.
- Little's law (effective depth) is computed for every run in `scripts/parse_fio.py`; the `psync iodepth=64` check gives effective depth 1.00.
- `scripts/check_docx_numbers.py` traces every number in the Word source of the report to data, raw logs or an explicit formula.
- Hypothesis commits `4f2fee8` (2026-10-16) and `69b59d1` (2026-10-22), made before the first experiment run, are cited in Section 9 of the report; check with `git log --format='%h %ci %s' 4f2fee8 69b59d1`.

Many fio JSON files in `data/raw/` record the original machine path in their `filename` field and were not altered.

## 10. Team and AI use

Team: Tiffany Cheng (Student A: safety guards, preconditioning, Exp 1 and 2), Marie Morales (Student B: Exp 3 and 4, knee analysis) and Alex Redd (Student C: Exp 5, 6 and 7, anomalies), as stated in Appendix A of the report. The AI tool used (Claude Code), errors found and corrections are also in Appendix A.
