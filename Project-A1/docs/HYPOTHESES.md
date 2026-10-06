# Hypotheses (written before results)

Each section is committed before the corresponding data is collected. Verdicts (supported, partly supported, refuted) are added in `report/REPORT.md`, never edited here, so the original wording stays visible in git history.

Facts used from `ENVIRONMENT.md`: Super core L1D 128 KB, L2 16 MB; Performance core L1D 64 KB, L2 8 MB; line 128 B; page 16 KB. A command-line process with default QoS ran on a Super core in a trial xctrace capture (Phase 1), so Mechanism 1 data is expected to describe a Super core unless QoS is set otherwise.

## Phase 2: Mechanism 1 (cache and TLB behavior)

**Question.** How do pointer-chase latency and streaming bandwidth depend on working-set size, stride and access pattern, and where are the L1, L2, SLC, DRAM and TLB boundaries?

**Microbenchmark design.** E1a: random single-cycle chase, one node per 128 B line, working set 4 KB to 2 GB, 2 points per octave. E1b: fixed number of nodes n (so a fixed number of cache lines), placed either packed (stride 128 B) or one per 16 KB page (stride 16512 B, which also spreads cache sets), n from 16 to 65536, to separate TLB reach from cache capacity. E1c: sequential, strided and random reads plus a STREAM-like triad, single thread, 16 KB to 1 GB.

**Controlled variables.** Same binary and flags, default QoS, AC power, Low Power Mode off, shuffled order, 2 warmups, at least 10 timed reps, fixed permutation seed, timed region at least 20 ms, page faults in timed region recorded.

**Metrics.** ns per dependent load (median, IQR, min), GB/s, minor page faults in the timed region.

**Predictions (stated now, numbers are guesses to be checked).**

- H1a (latency plateaus). On a Super core: L1 plateau up to about 128 KB at 1.2 ns or less; L2 plateau from 128 KB to 16 MB at roughly 3 to 6 ns; a further plateau beyond 16 MB inside the SLC at roughly 10 to 30 ns; DRAM plateau at roughly 80 to 130 ns for working sets well above the SLC. Boundaries appear within a factor of 2 of the sysctl cache sizes. The SLC size is not in sysctl, so its edge is an output, not an input.
- H1b (TLB). For equal node counts, one-node-per-page latency exceeds the packed layout once the number of pages exceeds TLB reach. I predict the first penalty (L1 dTLB miss, L2 TLB hit) at roughly 256 to 1024 pages and a larger penalty (page walk) beyond roughly 4096 to 16384 pages, i.e. footprints of 64 to 256 MB with 16 KB pages. Penalty at 65536 pages: at least 10 ns above the packed layout.
- H1c (bandwidth and prefetcher). Sequential read bandwidth from L2 and from DRAM is at least 3x the bandwidth of random-line reads at the same working set, because the hardware prefetcher covers sequential streams and random reads depend on memory-level parallelism alone. Strided reads fall between the two and degrade as stride grows. The STREAM-like triad agrees with the sequential read within 30% in the DRAM regime.
- H1 expected failure modes: working sets entirely inside one level show a flat curve and teach nothing about the others; a stride-linked chase is predicted by the prefetcher and yields a flat, misleadingly low curve (this is the AI-resilience checkpoint, measured first and kept as `data/raw/chase_naive_*`); first-touch page faults inflate timings if initialization does not touch every page.

**AI-resilience prediction (written before the first run).** The "obvious" chase (node i points to node i+1) will show a nearly flat latency curve of a few ns out to 1 GB, because sequential pointers are prefetchable. The corrected random single-cycle chase will show the steps predicted in H1a.
