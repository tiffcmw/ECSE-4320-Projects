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

## Phase 3: Mechanism 2 (scheduling and isolation via QoS)

**Disclosure.** Before writing this section I ran short pilot probes (about 10 runs, not kept as results, `data/raw/coretype_*.csv` holds the placement probes) to learn what the tools can do. The pilots showed: (a) on an idle machine every thread QoS class ran on Super cores; (b) `taskpolicy -c background` and `taskpolicy -b` placed a process on Performance cores and slowed a compute loop about 3x; (c) a single thread with QoS background got the same CPU share as one with interactive under a 36-thread hog. The hypotheses below were written after seeing these, so they are weaker evidence than the Mechanism 1 predictions; the full runs below test them with controlled repetition, and anything the pilots already suggested is marked "pilot-informed".

**Question.** What do thread QoS classes (`pthread_set_qos_class_self_np`) and process-level policies (`taskpolicy -b`, `-c`) change in throughput, tail latency, run-to-run variance and CPU share for a fixed-work compute-bound loop and a memory-bound (DRAM pointer-chase) loop, alone, with N threads, and under competing load?

**Microbenchmark design.** `qos_loop`: 200 chunks of fixed work (compute: 1 M dependent 64-bit multiply-adds per chunk; mem: 8000 dependent loads per chunk over a 256 MB random single-cycle chase per thread). Per-chunk times give p50, p99, max. Wall and thread CPU time are recorded; `cpu_over_wall` shows how much of the elapsed time the thread actually ran.

**Controlled variables.** Same binary, QoS set inside the worker thread before measurement, per-thread buffers, start barrier, warmup excluded, 15 reps (3 shuffled rounds x 5), AC power, thermal state recorded. Competing load is a separate process (36 spinning compute threads at QoS user-interactive) so it can be isolated from the measured process.

**Predictions.**

- H2a (idle, thread QoS; pilot-informed). With no competing load, throughput of the compute loop and the memory loop differs by less than 3% across the five thread QoS classes, and all classes run on Super cores.
- H2b (idle, process policy; pilot-informed). `taskpolicy -b` and `-c background` slow the compute loop by 2.5x to 4x and the DRAM chase by 2x to 4x versus plain, with run-to-run IQR/median under 10%.
- H2c (threads). With N <= 6 threads per-thread throughput matches N = 1 within 5%. At N = 12 and 18 per-thread compute throughput stays within 10% of N = 1 (Performance cores at default policy run this dependent-chain loop about as fast as Super cores, pilot-informed). At N = 36 (2x oversubscribed) per-thread `cpu_over_wall` falls to about 0.5 and p99 chunk time rises at least 10x.
- H2d (contention, thread QoS; pilot-informed). Under the 36-thread hog, thread QoS class does not change `cpu_over_wall` of the worker by more than 0.05 (all about 0.45 to 0.5), i.e. thread QoS is a hint, not isolation, for CLI processes.
- H2e (contention, process policy). Under the hog, `taskpolicy -b` reduces `cpu_over_wall` below 0.05 (isolation by starvation), and p99 chunk latency grows by more than 100x.
- Expected failure modes: QoS is a hint, so results can be non-deterministic; background policy can starve a benchmark so badly that fixed-work runs take minutes (handled by reducing chunk count and recording it); thermal throttling (flagged); placement is observed by xctrace only for sampled runs.

## Phase 4: Interaction (core tier x working-set size)

**Question.** Does moving a thread from a Super core to a Performance core change latency and bandwidth differently at different working-set sizes?

**Design.** Pointer-chase latency vs working set (E1a sizes) and bandwidth for three conditions: (S) plain process, observed on Super cores; (P) `taskpolicy -c background`, observed on Performance cores (but also a low-power policy, a confound); (18T) 18 plain threads, each with its own buffer, which lands threads on both tiers at default policy and is analyzed per thread by throughput signature. A fourth condition keeps `-c utility` (observed on Super) as a control for the clamp mechanism itself.

**Predictions (the original hypothesis, adapted).** H3: the Performance-to-Super ratio is smallest for L1-resident compute and widens when the working set exceeds the Performance L2 (8 MB) but not the Super L2 (16 MB), producing a ratio peak between 8 MB and 16 MB. Pilot-informed caveat: the pilots show a 3x slowdown for both compute and DRAM under policy (P), which suggests the ratio is nearly constant (a frequency effect), in which case H3 will be refuted for (P). For (18T), I predict that per-thread latency at 128 KB to 256 KB (above Performance L1D 64 KB, within Super L1D 128 KB) and at 8 to 16 MB splits into two groups, because the cache sizes differ by tier.
