# Notes on alignment, tail, stride and gather (Exp 3, 4), session `phase4`

Data: `data/raw/{tail,align,stride}_phase4.csv`, clock 4.58 GHz (`data/raw/freq_phase4.csv`), 0 throttled samples. Plots: `plots/exp3_tail_small_n`, `exp3_tail_mod16`, `exp3_alignment`, `exp4_stride_gather` (PNG and PDF). Numbers: `data/processed/phase4_summary_phase4.txt`.

## Alignment (SAXPY f32; both arrays shifted by the same offset)
- Vector build (`auto`): offsets that are multiples of 16 B (0, 16, 32, 48, 64, 96, 128) run at the same speed (within 1%). Every other tested offset (4, 8, 12, 20, 28, 60, 124, 132) is slower by 40% (32 KiB), 24% (4 MiB) and 21% (256 MiB). The penalty is the same for 4, 8, 12 and 60 B, so it is about 16 B alignment, not cache-line crossing (offsets 60 and 124 cross lines and cost no more than offset 4).
- Unrolled scalar: within 1% in L1, up to 6% slower for offsets that are 4 mod 8 in L2 and DRAM.
- H10 (under 5%) was wrong for the vector build. Possible cause, unverified: a 16 B or 32 B vector access that is not 16 B aligned is split into two accesses internally on this core. Not tested with counters. Limitation: x and y always shared the same offset; a relative misalignment between them was not tested.
- Consequence for the report: SIMD speedup claims assume 16 B aligned data. Malloc normally gives 16 B alignment, but subarray pointers (a view starting at element 1) lose up to 40% of in-L1 throughput.

## Tail (SAXPY f32 and f64, N = 1..160 and windows near 256, 1024, 4096, 16384)
- Fixed cost: an affine fit over N = 32..160 gives an intercept of about 2 ns (10 cycles) for f32 auto, 0.7 ns for unrolled scalar. The call overhead (0.9 ns, subtracted) has an uncertainty comparable to these intercepts.
- Per-element cost falls with N: f32 auto about 0.4 to 1.2 cycles per element for N <= 16, 0.35 at N = 32, 0.25 at N = 64, 0.19 at N >= 120 (asymptote). The cost around N = 4 to 16 is dominated by entry checks and the 4-wide and scalar epilogue loops.
- No visible N mod 16 or N mod 4 structure above N = 256 (residual variation under 1.5 ns). Below N = 64 the curve is irregular (dips at N = 32, 48, 64 for f32 auto); the code paths predicted from the disassembly (N < 4, N < 16) are not obviously visible as steps. No explanation is claimed.
- f64 auto equals unrolled scalar for N < 60 and is about 12% faster beyond, consistent with the f64 result of the locality sweep (two lanes).

## Stride and gather (f32)
- Compiler: stride >= 2 and gather are not vectorized by `auto` (cost-model remark); `auto_forcevec` produces `ld2.4s` de-interleave (stride 2), `zip1.2s` (stride 8), `ld1.s {v}[n]` lane inserts (gather), always with scalar or lane stores. `vecreports/asm/auto_forcevec_*`.
- In DRAM (512 MiB footprint) useful bandwidth for auto: 148.7 (s1), 56.0 (s2), 37.5 (s4), 20.3 (s8), 9.5 (s16), 1.0 GiB/s (s32), gather 5.1. SIMD gives no speedup at any stride >= 2 (the three builds are within a few percent).
- Anomaly (unverified): going from stride 16 (64 B) to 32 (128 B, one element per cache line) costs 10x per element (1.17 to 11.5 ns) although the line traffic only doubles. The L2-resident case (512 KiB) shows only a 1.2x step between s16 and s32. Possible causes: the hardware prefetcher stops tracking at 128 B strides, or every access is a new 16 KiB page group TLB walk; neither was tested.
- Gather in DRAM: 2.9 ns per element (13.5 cycles), 39x slower than unit stride.
