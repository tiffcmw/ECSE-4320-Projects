# Project 2: cache and memory performance profiling (ECSE 4320/6320)

Latency, bandwidth, concurrency, cache and TLB behavior of an Apple M5 Max (macOS, ARM64), measured with own C benchmarks. The deliverable is `report/ECSE4320_Project2_Report.docx` and the identical `report/ECSE4320_Project2_Report.pdf`: a self-contained document with all figures, tables, hypotheses, amendments, code excerpts and the AI-use note. Team notes: `report/WORK_SPLIT.md` (work split) and `report/DEFENSE_SHEET.md` (private).

## Rebuild

Requirements: Apple Silicon Mac, Xcode command line tools, Python 3 with numpy and matplotlib; pandoc and LibreOffice for the report. No sudo except the optional counter run.

```
scripts/run_all.sh                   # build, self-test, parse + validate + plot + report from the stored raw data (about 1 min)
COLLECT=quick scripts/run_all.sh     # first re-measure reduced sweeps (about 3 min)
COLLECT=full  scripts/run_all.sh     # first re-measure everything (about 30 min, quiet machine, AC power, 6 GB free memory)
sudo scripts/run_privileged.sh       # optional: powermetrics clock check and PMU counters (Exp 6, 7); then rerun scripts/run_all.sh
```

Raw CSVs are never overwritten: every collection writes `data/raw/<group>_<session>.csv`, a log and a metadata JSON. Parsing uses the newest full session; the counter run uses the suffix `-pmu`.

## Layout

| Path | Content |
|---|---|
| `src/` | `membench.c` (all kernels and sub-commands), `common.h`, `pmu.h` (optional kperf access) |
| `scripts/` | build, experiment driver, parse, validate, plot, `build_report.py`, `check_report.py` (recomputes the report numbers from the raw files), `make_docx.py` |
| `data/raw`, `data/processed` | per-round raw data and metadata; medians, min, max, n per configuration, tables, validation |
| `plots/` | figures (PNG at 220 dpi and PDF) |
| `report/` | final report (DOCX, PDF, markdown source in `parts/`), work split, defense sheet |
| `hypotheses.md` | predictions written before the benchmarks, with every later amendment |
| `docs/` | environment notes, plan, AI-use note |

## Honest limits

No Intel MLC, `perf`, pinning, governor, SMT control or huge pages on this platform; frequency is estimated; the SLC size is not exposed; counters need administrator rights (see the report, Appendix H).
