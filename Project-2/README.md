# Project 2: cache and memory performance profiling (ECSE 4320/6320)

Latency, bandwidth, concurrency, cache and TLB behavior of an Apple M5 Max (macOS, ARM64), measured with our own C benchmarks. The analysis is `report/REPORT.md`. Hypotheses written before any benchmark code or data are in `hypotheses.md` (see git history for the order: hypotheses, then code, then data). AI use is in `docs/AI_USE.md`.

## Quick start

Requirements: Apple Silicon Mac, Xcode command line tools (clang), Python 3 with numpy and matplotlib (no other packages). Nothing is installed system-wide and no `sudo` is used. For measuring: AC power, Low Power Mode off, no heavy background applications (check `ps -Ao pcpu,comm -r | head`). About 6 GB of free memory is needed for the loaded-latency runs.

```
scripts/run_all.sh                   # build, self-test, then parse + validate + plot from the newest raw data (about 1 min)
COLLECT=quick scripts/run_all.sh     # also re-measure reduced sweeps into new raw files (about 3 min)
COLLECT=full  scripts/run_all.sh     # re-measure everything (about 1 hour)
```

Individual steps: `scripts/build.sh` (clang -O2 -mcpu=native), `./bin/membench selftest`, `scripts/diagnostics.sh` (self-test log, huge-page probe, disassembly evidence), `scripts/run_exp.py --profile quick|full --sid ID [--only group1,group2]`, `scripts/parse.py`, `scripts/validate.py`, `scripts/plot.py`.

Raw CSVs are never overwritten: every collection writes `data/raw/<group>_<session>.csv`, a `.log`, and one `meta_<session>_<profile>.json`. Parsing and plotting use the newest full session (or the newest quick session if none exists). Use `P2_RAW`, `P2_PROC`, `P2_PLOTS` environment variables to redirect directories.

## Layout

| Path | Content |
|---|---|
| `hypotheses.md` | Pre-registered predictions (committed before code and data) |
| `report/REPORT.md` | Analysis tied to latency, bandwidth, concurrency, AMAT, Little's Law, limitations |
| `src/membench.c`, `src/common.h` | Benchmark harness: `chase`, `tlb`, `bw`, `pat`, `mlp`, `loaded`, `kern`, `dce`, `ramp`, `hugetest`, `freq`, `selftest` |
| `scripts/` | `build.sh`, `run_all.sh`, `run_exp.py` (experiment definitions, shuffled rounds), `meta.py`, `parse.py`, `validate.py`, `plot.py`, `xctrace_bottleneck.py`, `diagnostics.sh` |
| `data/raw/` | One CSV per experiment group and session, metadata JSON, logs, huge-page probe, disassembly |
| `data/processed/` | Median, IQR, min, max, n per configuration; `tables.md`, `validation.md`, `regions.json` |
| `plots/` | PNG and PDF figures |
| `docs/` | `ENVIRONMENT.md` (measurability), `PLAN.md`, `AI_USE.md` |

## Environment (details in `docs/ENVIRONMENT.md`)

MacBook Pro `Mac17,6`, Apple M5 Max (32-core GPU configuration), 36 GB unified memory, macOS 26.5.2, Apple clang 21.0.0. 18 cores: 6 Super (L1D 128 KiB, L2 16 MiB per 6-core cluster) and 12 Performance (L1D 64 KiB, L2 8 MiB per 6-core cluster). Cache line 128 B and page size 16 KiB (not the x86 64 B and 4 KiB). The system-level cache size is not exposed by `sysctl`.

## Deviations from the assignment text

| Assignment says | What was done and why |
|---|---|
| Intel Memory Latency Checker | Does not run on ARM macOS. Replaced by our own benchmarks: random single-cycle pointer chase (latency), NEON streaming and independent-load kernels (bandwidth), and a loaded-latency harness (one probe chase thread plus N sequential-read threads with optional injection delay). |
| `perf` counters for cache and TLB misses | Not available: no PMU API without root, no `perf` on macOS. Instruments (`xctrace`, CPU Counters template) runs without sudo but exports only cycles and pipeline-bottleneck fractions in guided mode, not miss counts. Cache and TLB behavior is inferred from timing signatures. Bottleneck fractions are reported only as supplementary evidence, labeled as such. No counter value is invented. |
| Pin threads, set governor, disable SMT, NUMA placement | macOS has no `taskset`, governor, or NUMA; the CPU has no SMT. Each worker sets `QOS_CLASS_USER_INTERACTIVE` inside its own thread to bias placement to Super cores. Placement is verified from the L1D/L2 capacity signature of the latency curve (Super 128 KiB / 16 MiB vs Performance 64 KiB / 8 MiB), not guaranteed. Frequency is automatic; see the clock-ramp pitfall. |
| 4 KiB pages vs huge pages | Not possible. `mach_vm_allocate` with `VM_FLAGS_SUPERPAGE_SIZE_2MB` and `SUPERPAGE_SIZE_ANY`, and `mmap` with the superpage flag, all fail with invalid argument on this system (`data/raw/hugetest.txt`). Page locality was varied instead (pages touched at fixed cache footprint, vs the 16 KiB page). |
| L3 latency | The M5 Max has a system-level cache (SLC) whose size is not exposed. It shows up as a latency ramp, not a plateau; an exact SLC size is not claimed. |
| Cycle conversion | Frequency is estimated by a dependent-add calibration after a warmup (about 4.5 GHz on a Super core); all cycle values are labeled estimates. |
| Read/write ratios "where supported" | Done as 100% read, 70/30, 50/50 (with separate and same-line streams), 100% write; write variants: regular stores, `stnp` (non-temporal pair hint), and `dc zva` (zero a block without fetching it). |

## Platform notes

- Timer: `mach_absolute_time`, 24 MHz tick (41.7 ns), so every timed region is at least 25 ms.
- Bandwidth peak used for sanity checks: 460 GB/s (published figure for the 32-core-GPU M5 Max, from secondary sources: Wikipedia "Apple M5" and a vendor-spec table; not checked against an Apple primary document). 614 GB/s is the 40-core-GPU figure.
- No fault is hidden: rows with page faults in the timed region are excluded and counted (`n_faulted` in processed data).
- Run order: groups run one after another; within a group each round runs every job in shuffled order with a new random seed (new permutations each round).

## Verification

`./bin/membench selftest` checks single-cycle chases, the TLB layout, the NEON read kernel against a scalar reference, store variants, mix-kernel coverage, pattern kernels against scalar references, the arithmetic kernels against a scalar reference, the clock, and the frequency estimate. `scripts/validate.py` checks monotonic latency, bandwidth against the published peak, L1 latency in cycles, repeatability, placement, Little's Law consistency, and thermal state; flags are reported in `data/processed/validation.md`.

## Reproduction check

On 2026-10-14 `COLLECT=quick scripts/run_all.sh` was run on a data-free copy of the tree (`git archive HEAD`, with the session data and processed files removed). It exited 0 in 2 min 18 s, passed the self-test, regenerated all 8 figures (PNG and PDF) and reported 0 validation flags. Headline values matched the full run: L1 0.66 vs 0.66 ns, L2 7.65 vs 7.64 ns, DRAM 109.4 vs 109.0 ns, `dc zva` 279 vs 273 GB/s. The quick profile has fewer thread counts, so its maximum bandwidth (290 GB/s at 16 threads) differs from the full run's (301 GB/s at 6 threads). A full-profile re-run from the clean copy was not done.

## Data sessions

`data/raw/*_20261014-0029.*` is the session behind the report. Sessions `20261014-0003` and `20261014-0015` are superseded by methodology fixes (see `hypotheses.md`, Amendments, and report Section 8) and are kept only for transparency; `parse.py` uses the newest full session.
