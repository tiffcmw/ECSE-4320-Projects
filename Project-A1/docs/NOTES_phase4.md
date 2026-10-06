# Phase 4 working notes (interaction: core tier x working set)

Data: `data/raw/inter_latency_*.csv`, `inter_bw_*.csv`, `inter_18t_*.csv`; processed `data/processed/inter_*.csv`; plots `plots/inter_latency_tier`, `inter_bandwidth_tier`, `inter_18threads`. 0 throttled rows; 11 faulted rows excluded. Placement: S and U observed 100% Super, P observed 100% Performance (`data/raw/coretype_*`, Phase 3 probes).

## Latency (E3a), median ns, S = plain Super, P = clamp background (Performance, low-power policy)
| working set | S | P | P/S |
|---|---|---|---|
| 4 KB to 32 KB (L1) | 0.65 | 2.24 | 3.4 |
| 128 KB | 0.66 | 14.7 | 22.4 |
| 256 KB to 1 MB | 2.6 | 17 | 6.6 |
| 2 to 4 MB | 7.1 to 7.6 | 17.7 to 20.2 | 2.5 to 2.7 |
| 8 MB | 8.1 | 90.6 | 11.2 |
| 16 MB | 22.8 | 133.5 | 5.9 |
| 128 MB to 2 GB (DRAM) | 105 to 110 | 342 to 377 | 3.2 to 3.4 |

- U (clamp utility) equals S within 1% except 1 MB (1.21x, one noisy point), so the clamp mechanism itself does not change latency; the effect in P comes from the background policy and Performance placement.
- The ratio is not constant. Baseline factor about 3.3x (L1-resident and DRAM-resident). Spikes sit where the tiers' cache sizes differ: 22x at 128 KB (Super L1D 128 KB vs Performance L1D 64 KB; P's L1 edge appears at about 64 to 92 KB), 11x at 8 MB (Performance L2 8 MB vs Super L2 16 MB). The 6.6x plateau between 256 KB and 1 MB reflects P's slower L2 (17 ns vs S 2.6 ns in the same range).
- H3 verdict: partly supported. Supported: the gap is smallest for L1-resident and DRAM-resident data (3.3 to 3.4x), and peaks at the tier cache-size boundaries (8 to 16 MB peak of 11x predicted and seen). Not supported as stated: the gap peaks at 128 KB (22x) more than at the L2 boundary, which the hypothesis did not predict, and the ratio never drops below 2.3x, so a policy/clock effect (about 3.3x) is mixed with cache effects and cannot be separated without frequency counters.

## Bandwidth (E3b), GB/s, S vs P
Sequential read: S/P 3.6x (16 KB), 4.1x (128 KB), 3.9x (1 MB), 3.6x (8 MB), 3.3x (16 MB), 2.8x (128 MB), 2.9x (1 GB). Random lines: 3.4x, 3.4x, 3.4x, 3.8x (8 MB), 4.3x (16 MB), 2.8x (128 MB), 2.2x (1 GB). Bandwidth ratios are flatter than latency ratios (memory-level parallelism hides part of the capacity mismatch) and lowest in DRAM (2.2x to 2.9x).

## 18 plain threads (E3c), per-thread ns per load, one buffer per thread
- 92 KB to 131 KB: median 2.6 to 3.2 ns but q1 0.73, q3 4.5: two groups (Super threads still L1-resident at 0.7 ns, others at about 4.5 ns), consistent with L1D 128 KB vs 64 KB at default policy. Evidence is per-thread latency signature, so placement is inferred, not pinned.
- At 8 MB to 12 MB: median 106 to 108 ns already; with 6 Super threads sharing one 16 MB L2 each effective share is under 3 MB, so shared-cache contention, not tier, dominates (confound). The 8 MB min of 78.6 ns shows some threads still got L2 hits.
- DRAM plateau drifts from 107 to 117 ns as footprint grows (more pages per thread).
