# Project A1: Advanced OS and CPU Feature Exploration

ECSE 4320/6320 Advanced Computer Systems. Two mechanisms and one interaction on an Apple M5 Max (6 Super + 12 Performance cores, 16 KB pages, unified memory, macOS 26.5.2):

1. Cache and TLB behavior (pointer-chase latency vs working set and stride, bandwidth vs access pattern).
2. Scheduling and isolation via thread QoS classes and process-level `taskpolicy`.
3. Interaction: core tier (Super vs Performance) x working-set size.

The write-up is `report/REPORT.md`. The AI-use note, including the flawed-design incident and a student verification checklist, is `docs/AI_USE.md`.

## Quick start

Requirements: Apple Silicon Mac, Xcode command line tools (clang), Python 3 with numpy and matplotlib (no pandas). Optional: full Xcode, used only for the placement probes (`xctrace`, invoked through `DEVELOPER_DIR`, no system-wide change). No `sudo` is needed or used.

Before running: plug in AC power, turn Low Power Mode off, close heavy applications. Do not touch the machine during a run; the harness records thermal state and flags disturbed runs.

```
./scripts/run_all.sh              # full profile, about 50 minutes, writes data/raw, data/processed, plots
QUICK=1 ./scripts/run_all.sh      # reduced sweeps, same code paths, roughly 15 minutes
```

Individual steps (each can be run on its own after `./scripts/build.sh`):

```
./scripts/build.sh                # clang -O2 -std=c17 -mcpu=native, builds build/*
./build/test_harness              # correctness tests (single-cycle chase, stats, clock, QoS)
./scripts/run_noise.sh            # E0 timer and noise floor
./scripts/run_mech1.sh            # E1: naive chase (AI-resilience before), random chase, TLB, bandwidth
./scripts/run_mech2.sh            # E2: QoS, process policy, threads, contention, placement probes
./scripts/run_interaction.sh      # E3: core tier x working set
(cd scripts && python3 exp_chase_diag.py)   # AI-resilience diagnosis (stride sweep)
./scripts/make_plots.sh           # processed CSVs and all plots from the newest raw files
```

Plots and processed tables always use the newest `data/raw/<prefix>_*.csv`. The committed raw files are the data behind the report; re-running adds new timestamped files next to them.

## Repository map

| Path | Content |
|---|---|
| `report/REPORT.md` | Final narrative with embedded plots, verdict per hypothesis |
| `docs/PLAN.md` | Experiment plan, parameter ranges, runtime estimates |
| `docs/HYPOTHESES.md` | Hypotheses written before each phase's data (see git history) |
| `docs/ENVIRONMENT.md` | Detected hardware, OS, tools, capabilities and limits |
| `docs/METHODOLOGY.md` | Timing, noise control, validity checks, counters available |
| `docs/AI_USE.md` | AI-use note, flawed-design incident, student verification log |
| `docs/NOTES_phase{2,3,4}.md` | Working notes with the numbers the report cites |
| `src/` | C harness: `platform.h` (clock, QoS), `harness.h` (stats, RNG), `chase_core.h`, `chase.c`, `bw.c`, `qos_loop.c`, `timer_noise.c` |
| `scripts/` | `build.sh`, `run_*.sh`, `exp_*.py` (experiment definitions), `runlib.py` (randomized order, thermal capture), `analyze.py`, `plot_*.py`, `probe_core_type.py` |
| `tests/` | `test_harness.c` |
| `data/raw/` | One CSV per run, with timestamp, config, thermal before and after, throttled flag |
| `data/processed/` | Median, IQR, min, max, n, n_throttled, n_faulted per configuration |
| `data/diagnostics/` | Disassembly of the chase hot loop |
| `plots/` | PNG and PDF figures |

## Platform notes

macOS has no `taskset`, `numactl`, cgroups, `perf`, hugetlbfs or THP; none are faked. Core placement is steered by QoS and `taskpolicy` and checked with Instruments, so it is observed, not guaranteed. `src/platform.h` isolates the clock, QoS and page-fault calls so a Linux track (`perf stat`, `taskset`, `numactl`, SMT and THP controls) can be added later without changing the benchmarks. It was not built.

## Verification

Checked on 2026-10-06 on the development machine (same hardware as `docs/ENVIRONMENT.md`):

- A data-free copy of the tree (code and docs only, produced with `git archive` excluding `data/raw`, `data/processed` and `plots`) was built and run with `QUICK=1 ./scripts/run_all.sh`. It exited 0, passed all tests, produced 11 raw files, 14 processed files and all 11 plots, with no failed runs.
- Headline numbers from the reduced run agree with the full committed run: naive chase at 1 GB 7.76 vs 7.79 ns, random chase at 1 GB 108.5 vs 110.5 ns, background-policy compute throughput 337 vs 344 M/s, default compute throughput 1100 vs 1142 M/s (within about 4%).
- Not checked: a full-profile re-run from the clean copy (the full data in this repository came from the original run), and a clone on a different machine. The student verification log in `docs/AI_USE.md` lists what to confirm personally.
