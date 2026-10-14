# Pre-registered hypotheses (Project 2)

Written on 2026-10-13 before any Project-2 benchmark code existed or ran. The commit timestamp of this file in git is the evidence; it must precede the raw data files. Any later change to a hypothesis is appended in the "Amendments" section at the end, never edited in place.

**Disclosure of priors.** The author of these predictions (Claude Code) did not measure anything for Project 2 before writing them. Priors come from (a) general knowledge of Apple Silicon memory systems and (b) the sibling Project-A1 report, which measured a random pointer chase on this same machine (L1 0.66 ns, L2 7 to 8 ns, DRAM about 105 to 111 ns, TLB penalties from 256 pages, a sequential chase that measured the prefetcher). Where a prediction below leans on A1 it says so; those are weaker evidence than a blind prediction. Experiments 2 to 4 and 6 to 8 were not run in A1.

Conventions: Super core = perflevel0 (L1D 128 KB, L2 16 MB). "Median" is over repetitions. Frequency `f` is the measured effective frequency from the calibration loop (a prediction of 4.0 to 4.7 GHz on a Super core, unverified).

## Placement and measurement validity (all experiments)

- **HV1.** A worker thread that sets `QOS_CLASS_USER_INTERACTIVE` on itself runs on a Super core. Test: the random-chase latency curve has its L1-to-L2 step at 128 KB (not 64 KB). Refuted if the step sits at 64 KB.
- **HV2.** Repetition noise (IQR/median) is at most 5% for L1, L2 and DRAM plateau points and may reach 15% in the SLC ramp (A1 saw 12 ns IQR at 47 MB).
- **HV3.** Every raw bandwidth value is below 460 GB/s (published peak for the 32-core-GPU M5 Max; 614 GB/s is the absolute upper bound). A value above 460 GB/s in a footprint beyond the SLC is a measurement error and will be investigated; above it with a cache-resident footprint is expected.

## Exp 1: zero-queue baselines (random chase, one thread)

- **H1a.** L1 hit latency 3 to 5 cycles, i.e. 0.6 to 1.2 ns (A1: 0.66 ns).
- **H1b.** L2 latency 12 to 40 cycles, i.e. 3 to 9 ns; the plateau sits near 16 MB capacity (one active core can use the whole 16 MB L2). A1 saw 7 to 8 ns and an unexplained 2.6 ns step between 128 KB and 1 MB; I predict that step recurs.
- **H1c.** The SLC region (16 MB up to some hundreds of MB) is a ramp, not a clean plateau (A1), with values between L2 and DRAM. An SLC size cannot be read exactly; I predict the ramp ends before 512 MB.
- **H1d.** DRAM latency (1 GiB footprint, random lines) is 90 to 130 ns, 400 to 600 cycles.
- **H1e.** Latency is monotonic non-decreasing with working set within noise (5%).

## Exp 2: pattern and granularity

- **H2a.** Sequential pointer-chase at 128 B stride in a DRAM-resident footprint is at least 5x faster per node than the random chase (prefetcher; A1 saw 14x).
- **H2b.** Random chase latency does not depend on node stride for strides of 128 B and up (flat within 10% once the footprint is fixed at 1 GiB), because each node is a different line anyway. TLB effects raise the large-stride points modestly.
- **H2c.** A sequential chase with growing stride loses its prefetch benefit gradually; at 16 KB stride (one node per page) it is still at least 2x faster than random (A1 saw the prefetcher tracking constant strides to 64 KB).
- **H2d.** Single-thread sequential read bandwidth in DRAM is 60 to 140 GB/s (A1 saw 98 GB/s with NEON); random-line (independent loads) bandwidth is 20 to 70% of sequential.
- **H2e.** Useful-byte bandwidth for a 16 B access at stride 128 B or larger is about 1/8 of the full-line rate (the 128 B line is fetched whole); stride 64 B behaves like stride 128 B for line-count purposes (two accesses per line).

## Exp 3: read/write mix

- **H3a.** Single-thread throughput in a DRAM-resident footprint orders as 100% read >= 70/30 >= 50/50 >= 100% write in application-visible GB/s, with 100% write between 0.4x and 1.0x of read.
- **H3b.** With write-allocate, 100% write moves more DRAM bytes than the application writes; a traffic-corrected rate (writes counted twice) for 100% write is closer to the read rate than the uncorrected one. This is a model, not a measurement (no DRAM counters).
- **H3c.** Non-temporal stores (`stnp`) change write throughput by less than 15% (the hint may be ignored in cached hierarchies). `dc zva` (zero a line without reading it) is at least 1.3x faster than plain stores if user-mode DC ZVA is permitted, which would be direct evidence of write-allocate cost.
- **H3d.** Under a fixed background load, a write-heavy mix raises loaded read latency more than a read-only mix of the same application-visible rate.

## Exp 4: intensity sweep and Little's Law

- **H4a.** One thread running K independent random chains: throughput rises roughly linearly with K up to a plateau between K = 16 and 64 outstanding lines; the plateau throughput is 20 to 60 GB/s. At K = 1 the rate is 128 B / latency, about 1.2 GB/s.
- **H4b.** Multi-thread streaming reads: aggregate bandwidth saturates at 55% to 85% of 460 GB/s (250 to 390 GB/s) with 8 to 14 threads; adding threads beyond saturation does not raise throughput.
- **H4c.** Loaded latency measured by an independent probe thread stays within 1.3x of idle latency up to about 50 to 60% of the saturation bandwidth, then rises, reaching at least 2x idle at saturation (the knee).
- **H4d.** Little's Law check: in-flight lines `N = BW x L_loaded / 128 B` is system-wide 200 to 700 lines at the knee and does not keep growing past it; BW grows at constant N only if latency is constant, so beyond the knee BW stays flat while L rises.
- **H4e.** More than 6 bandwidth threads spill onto Performance cores and the per-thread rate falls.

## Exp 5: working-set sweep

- **H5a.** L1 edge at 128 KB (+/- one sweep step), L2 edge at 16 MB (+/- one step), DRAM plateau by 512 MB. The same sweep for single-thread read bandwidth falls from above 300 GB/s (L1) to 100 GB/s class (DRAM). The bandwidth edge locations match the latency edges.

## Exp 6: cache-miss impact on kernels

- **H6a.** For z[i] = x[i]*y[i] and y[i] = a*x[i] + y[i] (f32, unit stride), ns per element is flat while the footprint is below the L2 size and rises beyond it; the rise ratio between L1-resident and DRAM-resident is 3x to 15x.
- **H6b.** Stride-k element access (k x 4 B) raises ns per element until k x 4 B reaches 128 B (k = 32), after which it is flat; the plateau is at least 5x the unit-stride DRAM cost.
- **H6c.** A random gather (permuted index) in DRAM is at least 8x slower per element than unit stride.
- **H6d.** An AMAT-style prediction built only from the measured latency curve (miss ratio from the footprint/line model, hit and miss latencies from Exp 1, divided by the measured MLP) explains runtime within a factor of 2 for the random cases and fails (under-predicts speed by more than 2x) for unit stride where the prefetcher dominates. No hardware counter is used; miss behavior is inferred.
- **H6e.** Both kernels match a straightforward scalar reference bit-for-bit for multiply and within 1 ulp for the fused form.

## Exp 7: TLB-miss impact

- **H7a.** Holding the number of lines fixed (cache footprint identical), touching one line per page instead of packed lines adds latency once the number of distinct 16 KB pages exceeds the L1 DTLB reach. Onset between 128 and 512 pages (2 to 8 MB reach); A1 saw +1.3 ns at 256 pages.
- **H7b.** A second, larger step occurs between 2048 and 8192 pages (L2 TLB reach of 32 to 128 MB), and the penalty at 65536 pages is 10 to 30 ns (A1: 18.5 ns). Penalty is non-decreasing in pages.
- **H7c.** Huge-page comparison cannot be done on macOS; no claim about it will be made.

## Exp 8: benchmark pitfalls

- **H8a.** A "DRAM bandwidth" test with an 8 MB array (L2-resident) reports at least 2x the true DRAM bandwidth.
- **H8b.** A sequential (non-random) pointer chase of a 1 GiB footprint reports at least 5x lower latency than the random chase (A1 saw 14x).
- **H8c.** A kernel whose result is never used is removed by `-O2`: it reports a time near zero or a bandwidth above 1 TB/s. Adding a sink restores a physically plausible value.
- **H8d.** After 2 s of idle, the first 10 ms of a compute loop is at least 1.1x slower than steady state (DVFS ramp). This is the least certain prediction; M-series ramp is fast and the effect may be absent. If absent, it is reported as a negative result.

## Amendments

**2026-10-14, after the first full collection (session 20261014-0003, commit 8fd3520).** No hypothesis above was changed. Three methodology defects were found in that session's data and fixed before a second full collection; the first session's raw files stay in the repository, superseded:

1. The loaded-latency harness slept 200 ms before its measurement window, so the probe core's clock ramped down. Idle latency read 119 ns against 109 ns from the chase sweep. Fix: the probe thread spins during the warmup instead.
2. The stride sweeps kept the footprint in bytes fixed, so at 4 KiB and 16 KiB strides only 8 to 32 MiB of distinct lines were touched and they stayed cache-resident (random chase at 16 KiB stride: 29 ns instead of about 109 ns). Fix: the number of distinct lines is held at 1 Mi (128 MiB of lines) for every stride; the 16 KiB stride was dropped (it would need 16 GiB).
3. The TLB sweep included a one-node cycle that read 0.12 ns (below L1 latency). That degenerate point is no longer collected; it is reported as an anomaly.

These were found by reading the first session's results, so the hypotheses for Exp 2 stride points and Exp 4 idle latency were not tested blind against the corrected design. Predictions H2b and H2c refer to the corrected design.
