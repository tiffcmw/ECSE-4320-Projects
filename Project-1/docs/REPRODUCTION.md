# Clean-clone reproduction record (2026-10-06)

Procedure: `git clone` of the repository into an empty directory, then in `Project-1/`:

1. `scripts/run_all.sh` (default mode): built 7 build variants x 12 kernels x 3 dtypes (rebuilt from source), 64326 correctness checks, 0 failures; regenerated the vectorization reports and all 15 plots from the committed raw data. `data/processed/` tables were byte-identical to the committed ones (`git diff --stat -- data/processed` empty). PDF files differ only by embedded timestamps.
2. `COLLECT=quick SID=cc_quick scripts/run_all.sh`: re-measured a reduced version of every experiment (tests, session characterization, sweeps A to D, alignment, tail, stride, FMA peak, triad, multi-process triad, aliasing, accuracy, naive benchmark), then re-plotted from the new CSVs. Completed with exit code 0, 0 throttled samples in the sweep, 15 plots written.

Agreement between the quick re-measurement and the committed full-run values (single machine, same day, so this shows repeatability, not independence):

| quantity | committed full run | clean-clone quick run |
|---|---|---|
| f32 SAXPY auto vs unrolled scalar, L1 (32 KiB) | 2.08x | 2.07x |
| f32 SAXPY auto vs unrolled scalar, 256 MiB | 1.35x (1 GiB) | 1.31x |
| fmla.4s peak | 145.8 GFLOP/s (3.99 per cycle, 20 accumulators) | 145.1 GFLOP/s (3.96, 20 accumulators) |
| fmla.2d peak | 72.3 GFLOP/s | 72.5 GFLOP/s |
| single-process triad, 256 MiB to 2 GiB | 121.8 to 123.4 GiB/s | 121.7 to 122.6 GiB/s |
| naive N3 (first touch) vs fixed | 81 vs 148 GiB/s | 84.5 vs 147.4 GiB/s |

The quick CSVs stayed in the scratch clone and are not committed (they would duplicate the full data). Limits of this check: same machine, same macOS and compiler; a different Apple chip would give different absolute numbers (cache sizes, clock, pipes) and some of the unexplained effects may differ.
