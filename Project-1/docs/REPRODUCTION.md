# Clean-clone reproduction record (2026-10-07, commit 11b314d)

Procedure: `git clone` of the repository into an empty directory, then in `Project-1/`:

1. `scripts/run_all.sh` (default mode): rebuilt every kernel from source, ran 75018 correctness checks in the main suite and 5544 in the suite for the added kernels (0 failures), regenerated the vectorization reports and all 21 plots from the committed raw data. `git diff -- data/processed` was empty: every processed table is byte-identical to the committed one. PDF files differ only by embedded timestamps.
2. `COLLECT=quick SID=cc_quick2 scripts/run_all.sh`: re-measured a reduced version of every experiment (tests, session characterization, sweeps A to D, alignment, tail, stride, FMA peak, triad, multi-process triad, aliasing, accuracy, naive benchmark, pointer chase, page-granular chase, traffic accounting, dot decomposition, relative misalignment, stride-jump probes), then re-plotted from the new CSVs. Exit code 0, 0 throttled samples, 21 plots written, 119 s in total (one pass of 3 samples per point instead of 3 passes of 5).

Agreement between the quick re-measurement and the committed full-run values (same machine, same day, so this shows repeatability, not independence). The session clocks were 4.54 to 4.57 GHz in the quick run against 4.58 GHz (main sessions) and 4.55 GHz (`ext1`).

| quantity | committed full run | clean-clone quick run |
|---|---|---|
| f32 SAXPY auto vs unrolled scalar, L1 | 2.08x (32 KiB) | 2.10x (16 KiB point) |
| f32 SAXPY auto vs unrolled scalar, large footprint | 1.35x (1 GiB) | 1.30x (1 GiB) |
| fmla.4s peak | 145.8 GFLOP/s (3.99 per cycle, 20 accumulators) | 146.0 GFLOP/s (4.02, 21 accumulators) |
| fmla.2d peak | 72.3 GFLOP/s | 71.9 GFLOP/s |
| single-process triad, 256 MiB to 2 GiB | 121.8 to 123.4 GiB/s | 120.6 to 123.2 GiB/s |
| naive N3 (first touch) vs fixed | 81 vs 148 GiB/s | 82.2 vs 136.9 GiB/s |
| chase latency, L1 / DRAM | 0.66 ns / 110.8 ns | 0.65 ns / 110.3 ns |
| first page count above 1.4x L1 latency (page-granular chase) | 181 | 181 |
| dot f32 L1: chain-break gain / SIMD gain / total | 8.4x / 1.67x / 14.0x | 8.3x / 1.81x / 15.0x |
| relative misalignment, 32 KiB: y only 4 B / both 4 B / x 4 B, y 8 B | 1.26 / 1.45 / 1.39 | 1.27 / 1.41 / 1.40 |
| stride 16 / 32 / 48 at 512 MiB (ns per element) | 1.17 / 11.5 / 3.96 | 1.16 / 11.5 / 3.90 |
| counted bandwidth at 256 MiB: SAXPY / triad / out-of-place SAXPY | 146.5 / 117.4 / 121.7 GiB/s | 147.1 / 123.1 / 123.6 GiB/s |

Deviations: `copy` at 256 MiB was 82.7 GiB/s in the quick run against 116.2 GiB/s in the full run (one pass of 3 samples; not investigated, so single-pass quick values are noisier than the full run); the x-only 4 B misalignment penalty was 1.00 in the quick run against 1.06 (the effect is small and sits near the noise of a 3-sample point); the naive N3 corrected value was 8% lower. The quick CSVs stayed in the scratch clone and are not committed (they would duplicate the full data).

Limits of this check: same machine, same macOS and compiler; a different Apple chip would give different absolute numbers (cache sizes, clock, pipes) and some of the unexplained effects may differ. The report PDF is built separately with `scripts/make_report_pdf.py` (needs `pip install markdown` and Google Chrome).
