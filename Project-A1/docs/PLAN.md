# Plan

Hardware: Apple M5 Max, 6 Super + 12 Performance cores (see `ENVIRONMENT.md`). The assignment's "P vs E" wording is mapped to **Super vs Performance** (user-approved in Phase 0).

## Mechanisms and interaction

1. **Mechanism 1: cache and TLB behavior.** Question: how does access latency and bandwidth depend on working-set size, stride and access pattern, and where are the L1, L2, SLC, DRAM and TLB boundaries on a 16 KB-page system?
2. **Mechanism 2: scheduling and isolation via QoS.** Question: how do QoS classes change throughput, latency distribution and variance for fixed-work compute-bound and memory-bound loops, alone and under background load?
3. **Interaction: core tier x working-set size.** Question: does the QoS-steered core tier change where and how steeply latency and bandwidth degrade as the working set grows?

## Experiments

| ID | Experiment | Sweep | Metrics | Reps |
|---|---|---|---|---|
| E0 | Timer resolution and overhead; run-to-run noise floor | back-to-back clock reads; fixed loop 100 times | tick, overhead ns, CV | 100 |
| E1a | Pointer-chase latency vs working set (random single-cycle permutation, one node per cache line) | 4 KB to 2 GB, 2 points per octave (about 40 sizes) | ns per load, min/median/IQR | 11 |
| E1b | Latency vs stride at fixed large footprint, to expose TLB reach (page = 16 KB) | stride 128 B to 64 KB, footprints 64 MB and 1 GB | ns per load | 11 |
| E1c | Bandwidth: sequential, strided, random; STREAM-like triad as cross-check | working sets 16 KB to 1 GB | GB/s | 11 |
| E1x | **AI-resilience:** naive stride-linked chase (prefetcher-friendly), then corrected random chase | same as E1a | ns per load, before/after | 11 |
| E2a | Compute loop (dependent FP chain) and memory-bound loop at each QoS class, 1 thread | 4 QoS classes | throughput, wall vs CPU time, CV | 15 |
| E2b | Same with N threads (N = 1, 4, 6, 12, 18) | QoS x N | throughput, per-thread spread | 15 |
| E2c | Same with competing background load (spinning threads at background QoS, and at user-initiated) | QoS x load on/off | throughput, latency p50/p99 | 15 |
| E2x | **AI-resilience candidate:** threads created before QoS set (QoS has no effect) vs QoS set inside the thread | QoS classes | throughput | 15 |
| E3a | Latency vs working set per QoS class (Super-biased vs Performance-biased) | E1a sizes x 2 to 4 QoS classes | ns per load, ratio gap | 11 |
| E3b | Bandwidth vs working set per QoS class | E1c sizes x QoS | GB/s | 11 |
| E3c (if time) | QoS x concurrent memory-bandwidth hog | QoS x hog threads 0/2/6 | latency, GB/s | 11 |

Core-tier identification is a first step of Phase 3 (E2-pre): measure per-QoS single-thread compute throughput and L2-capacity signature (latency step near 8 MB vs 16 MB). A tier is labeled "inferred" from this signature, never "pinned".

## Pre-registered hypotheses

Formal text, with predicted numbers, is written to `docs/HYPOTHESES.md` before each phase's data is collected. Summary:

- H1 (cache/TLB): latency shows plateaus at L1, L2, SLC, DRAM; the prefetcher makes sequential bandwidth far above random; stride beyond the 16 KB page raises latency once the footprint exceeds TLB reach.
- H2 (QoS): compute-bound throughput differs little across QoS classes when the machine is idle, but background QoS is slower and noisier, and the gap grows under competing load.
- H3 (interaction): the tier gap is smallest for L1-resident work and widens once the working set exceeds the smaller tier's L2 (8 MB) but not the larger (16 MB).

Expected failure modes: working sets inside one cache level; the compiler or prefetcher defeating the chase; QoS being only a hint, giving non-deterministic placement; thermal throttling on long sweeps.

## Methodology defaults

clang `-O2`, single `mach_absolute_time` clock, volatile sink or asm barrier, one-cycle assertion on every chase permutation, 11 to 15 repetitions per point with 2 warmups discarded, median + IQR + min, randomized configuration order, `caffeinate -dimsu`, thermal state recorded before and after each run, flagged runs excluded from medians but kept in raw data.

## Estimated runtime

| Phase | Compute time |
|---|---|
| 1 harness and noise | 5 min |
| 2 (E1a, E1b, E1c, E1x) | 40 to 60 min |
| 3 (E2a, E2b, E2c, E2x) | 40 to 60 min |
| 4 (E3a, E3b, optional E3c) | 40 to 90 min |
| 6 clean re-run check | reduced "quick" profile, 10 min |

`run_all.sh` will offer `QUICK=1` for the reduced profile.

## Commands needing sudo (to be listed for the user, never run silently)

- `sudo powermetrics --samplers cpu_power,thermal -i 1000 -n <N>` to observe per-cluster activity while a QoS test runs (placement evidence). Requested in Phase 3, only if the user approves.

## Optional Linux track

A platform layer (`src/platform.h`) isolates the clock, QoS and thread setup so a `linux/` directory can be added later with `perf stat`, `taskset`, `numactl`, SMT and THP controls. Not built now.

## Open items

- Confirm `xctrace` CPU counters work (Phase 1). If not, state "no PMU access" in the report.
- Confirm which QoS classes reach which tier (Phase 3 first step). If they all land on the same tier, E3 falls back to the QoS x bandwidth-hog interaction and the report says why.
