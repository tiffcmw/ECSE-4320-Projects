# Project 3: SSD performance profiling (Apple M5 Max, internal NVMe, APFS)

Everything runs against **one disposable 32 GiB file** inside `scratch.noindex/`. No raw device is ever touched. Results and interpretation are in `REPORT.md`; predictions made before data collection are in `HYPOTHESES.md`; AI use is in `AI_USE.md`.

## Reproduce end to end

```
brew install fio smartmontools          # fio 3.43 and smartctl 7.5 were used
bash scripts/run_all.sh                 # about 3 hours, about 4 TB of SSD writes (see below)
bash scripts/cleanup.sh                 # deletes only the test file and marker files
```

Run conditions: **charger plugged in, lid open, nothing else running** (the stages abort a run if the Mac leaves AC power or sleeps; see Safety). `run_all.sh` waits for AC power, then runs: engine check, 32 GiB precondition, direct-I/O check (stops everything if `direct=1` looks cache-like), Exp 1 to 7, a drift time series and an Exp 4 replicate, then parses, tabulates, plots and builds `REPORT.md` from `REPORT.template.md`. Python needs matplotlib and numpy; `run_all.sh` makes `.venv/` if it is missing. Stage drivers can be run singly (`scripts/run_02_exp1_exp2.sh` and so on); `SMOKE=1 bash scripts/run_0X_*.sh` runs 3 s versions into `data/smoke/` (git-ignored).

## Layout

| Path | Contents |
|---|---|
| `fio/` | one job file per experiment; header comments list fixed and varied knobs; knobs arrive as environment variables from the drivers |
| `scripts/common.sh` | safety guards, per-run validity checks, health logging |
| `scripts/run_*.sh` | drivers: `00` precondition, `01` direct-I/O check, `02` Exp 1+2, `03` Exp 3+4, `04` Exp 5, `05` Exp 6+7 (+ drift check), `06` drift series, `07` Exp 4 replicate, `run_engine_check.sh`, `run_all.sh`, `wait_for_ac.sh`, `cleanup.sh` |
| `scripts/parse_fio.py` | fio JSON to `data/processed/all_runs.csv` and `summary.csv` (mean, sd, min, max over trials; Little's-law check per run) |
| `scripts/make_tables.py`, `check_smart_reads.py`, `analyze_state_split.py`, `plots.py`, `build_report.py` | tables, SMART cross-check, analysis of the two IOPS levels (existing data only), figures, `REPORT.md` assembly |
| `scripts/export_docx_data.py`, `scripts/docx/make_docx.js`, `scripts/check_docx_numbers.py` | the Word report `Project3_SSD_Report.docx` (tables from `data/processed`, figures from `plots/docx/`) and a trace of every number in it to the data (`data/processed/docx_number_trace.md`); needs `cd scripts/docx && npm install docx` and pandoc |
| `data/raw/` | untouched fio JSON, one file per run, name = `exp__knob=value__...__tN.json`; `health/` has before/after snapshots per stage; `invalid_sleep_2026-10-22/` holds quarantined runs |
| `data/processed/` | CSVs and generated markdown tables |
| `plots/` | PNG and PDF figures |

## Safety measures (all in `scripts/common.sh`)

- `guard_path` resolves the real path and aborts unless the target is inside `scratch.noindex/`; `/dev/*` and symlinks are refused. It runs before every fio call.
- Free-space check: aborts if less than 20% of the volume would remain after the test file.
- `check_power` before every run: refuses battery power and Low Power Mode. After every run the result is checked and moved to `data/raw/invalid/` if the Mac left AC power or the run took longer than runtime + ramp + 45 s (system sleep). Each driver holds a `caffeinate -ims` assertion for its lifetime. **These last guards were added after the first Exp 2 write results were ruined by a sleep (REPORT, Anomaly 2).**
- `cleanup.sh` removes only named files (`testfile.bin`, `engine_check.bin`, the precondition marker); no recursive deletes anywhere.
- Health context before and after every stage (`data/raw/health/`): `smartctl` (model, firmware, temperature, wear, host bytes read and written), `pmset` (power source, Low Power Mode, thermal), `df`, top CPU processes, macOS and fio versions.
- **`smartctl` works on this drive without sudo** (`smartctl -a disk0`): temperature, wear and data-unit counters are readable. It does not give SSD temperature during a run more finely than 10 s sampling, and PCIe link state is not exposed. No privileged command was run.

## Engines, direct I/O and what was not available

- Available on macOS: `psync` (and other synchronous engines), `posixaio`, `mmap`. **`libaio` and `io_uring` do not exist on macOS**; this is detected by `run_engine_check.sh` and recorded in `data/raw/engine_check_macos27.0.1/engines.txt`. The fallback is `psync` with `numjobs=N` (effective depth N) and `posixaio` with `iodepth=N`; neither is assumed to give the configured depth, Little's law is checked for every run.
- fio runs at most about 16 jobs at once on this Mac (`kern.sysv.shmall` is 4 MB system-wide: "failed to setup shm segment"), so `psync` depths stop at 16. On macOS 27.0.1 `posixaio` reaches depth 256 in one process (`kern.aioprocmax=256`); on 26.5.2 it was capped at 16 (the OS changed mid-project, REPORT Anomaly 3).
- Direct I/O: `direct=1` sets `F_NOCACHE`. Verified by behaviour, not by tracing: (1) `direct=1` vs `direct=0` on the same file gives 87x latency difference, and the check script stops the campaign if `direct=1` looks cache-like; (2) SMART "Data Units Read" is never lower than fio's byte count (`data/processed/tables/smart_read_check.md`); (3) fio write bytes match SMART "Data Units Written" to 0.01%.

## Methodology record

SSD, filesystem, OS and CPU versions, file size and offset range, data pattern, power and thermal state, background load, repetitions, runtime and ramp per job and the preconditioning procedure are listed in the Methodology section of `REPORT.md` and are not repeated here.

## SSD write volume (corrected)

The first estimate (150 to 300 GiB) was far too low, because the drive writes at 10 to 12 GB/s. Measured by the SMART counter:

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

A clean `run_all.sh` writes about 4 TB. Total drive wear was not measurable (SMART "Percentage Used" 0%).

## Notes and known limits

- Two stable performance levels (about 189 k and 222 k IOPS for the same read workload) appeared at different times; cause unknown (REPORT, Anomaly 1). Compare numbers within an experiment, and treat cross-experiment absolute differences under about 17% with care.
- Sustained write is a single run capped at 2.2 TB (4 x 512 GiB) or 300 s; it ended at 2.2 TB after 198 s.
- Spotlight is excluded by the `.noindex` directory name. Time Machine was idle; no local snapshots existed.
