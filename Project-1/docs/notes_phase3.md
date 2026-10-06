# Phase 3 notes (Exp 1, 2, 5), session `phase3`, 2026-10-06

Data: `data/raw/sweep_phase3_{A,B,C,D}.csv` (25530 samples, 15 per point: 3 passes x 5 reps, shuffled order, 0 samples with thermal pressure >= 1), clock 4.586 GHz (IQR half-width 0.014, `data/raw/freq_phase3.csv`). Plots: `plots/exp1_sweep_f32.*`, `exp1_sweep_f64.*`, `exp2_saxpy_locality.*`, `exp5_dtype.*`, `exp5_elements_per_ns.*`. Speedup table: `data/processed/exp1_speedup_phase3.csv`. Working set counts all arrays (SAXPY: x and y). Cache sizes are the Super-tier sysctl values; which tier runs the code is unverified.

## Findings
1. Baseline matters more than lane count. Against the assignment-defined `scalar` build (not unrolled) f32 SAXPY speeds up 5.2x in L1 and 3.0x in DRAM. Against the unrolled scalar baseline it is 2.1x and 1.35x. The headline numbers in the report use `scalar_unroll8` and show `scalar` as a second curve.
2. f32 SAXPY: L1 about 270 GiB/s (0.19 cycles per element), then a sharp drop at 128 KiB to about 150 GiB/s (0.34 cycles per element) that stays flat to 2 GiB. The unrolled scalar curve moves from 125 to 112 GiB/s.
3. Mul (three arrays) decays gradually between 128 KiB and about 2 MiB, then is flat at about 120 GiB/s (f32).
4. f64: vectorized and unrolled-scalar versions are within 7% for SAXPY and mul in L1 (cycles per element 0.40 vs 0.43): with two lanes the vector loop moves the same bytes per cycle as the unrolled scalar loop, so the limit appears to be memory-operation throughput rather than arithmetic (inferred from the cycle counts, not measured with counters).
5. Dot: plain `-O3` (in-order reduction) is 1.46x faster than the unrolled scalar and flat from L1 to DRAM at about 15.6 GiB/s, so it is bound by the dependent `fadd` chain (about 2 cycles per element) and never reaches a memory limit. Fast-math reaches 13.6x (f32) and 6.7x (f64) in L1 and 10x and 5x in DRAM. These far exceed the lane count because the scalar loop is latency bound at about 3 cycles per element, not because of lanes. u32 dot vectorizes without fast-math: 5.9x in L1.
6. `native` equals `auto` within 3%.
7. Noise: median CV 1.8%. A few points have larger spread (CV up to 47%), visible as long error bars in a few small-size points (for example f32 SAXPY near 12 to 16 KiB).

## Anomalies (explanations unverified)
- No visible L2 (16 MiB) or SLC boundary for SAXPY: 150 GiB/s at 256 KiB and 143 GiB/s at 2 GiB. Plausible but untested explanations: (a) one core cannot draw more than about 150 GiB/s from anything outside L1, so L2, SLC and DRAM are indistinguishable for one thread; (b) the hardware prefetcher fully hides DRAM latency for pure streams. Test planned in Phase 5: a STREAM-style triad and a pointer-chase would show whether DRAM-level bandwidth differs when access is not a pure stream. The assignment's premise that SIMD gain compresses toward 1x in DRAM was only seen for f64 and mul.
- The dip in the f32 SAXPY auto curve near 16 to 32 KiB (about 255 GiB/s vs 275) is repeatable across fastmath and auto but is not explained.
- 1 GiB-scale working sets show a slow decline (150 to 143 GiB/s); possibly TLB reach with 16 KiB pages (unverified).
