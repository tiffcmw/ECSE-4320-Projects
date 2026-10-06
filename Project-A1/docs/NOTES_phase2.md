# Phase 2 working notes (Mechanism 1 results, source for REPORT.md)

Data: `data/raw/chase_naive_*.csv`, `chase_random_*.csv`, `chase_tlb_*.csv`, `bw_*.csv`; processed medians in `data/processed/`. Plots: `plots/mech1_*.png`. Default-QoS process, observed on a Super core in the Phase 1 xctrace trial. 0 throttled rows. 11 of 585 random-chase rows had timed page faults (1 to 1582) and are excluded and counted in `n_faulted`.

## H1a latency plateaus (partly supported)
- L1: 0.66 ns up to 92 KB, jump at 128 to 256 KB, matching Super L1D 128 KB. 0.66 ns is the known-answer region (few cycles).
- Intermediate plateau 2.6 ns from 256 KB to about 1 MB, then 7.1 to 7.9 ns from 2 MB to 8 MB. Predicted L2 at 3 to 6 ns: the 7 to 8 ns L2 plateau is higher than predicted. The 2.6 ns step between 256 KB and 1 MB is not explained by sysctl; interpretation (a faster private portion of L2 or L1-TLB effect) is an open question and is labeled inferred.
- Step to 23 ns at 16 MB, 38 to 76 ns at 32 to 48 MB, DRAM plateau 105 to 111 ns from 128 MB. No distinct SLC plateau: the 16 to 128 MB region is a ramp, so SLC size cannot be read off cleanly.

## H1b TLB (supported for the first penalty, partly for the second)
One node per page vs packed (median ns): 256 pages 2.0 vs 0.7; 2048 pages 7.0 vs 2.6; 4096 pages 11.9 vs 2.6; 65536 pages 26.7 vs 8.2. First penalty at 256 pages (predicted 256 to 1024). Large penalty arrives at 2048 to 4096 pages, earlier than predicted 4096 to 16384. Penalty at 65536 pages is +18.5 ns (predicted at least +10 ns).

## H1c bandwidth (partly supported)
Single thread, GB/s at 1 GB: seq read 90.7, random lines 22.7 (ratio 4.0x, prediction of at least 3x holds in DRAM). At 8 MB: seq 116 vs random 96 (1.2x), so the prefetcher advantage is a DRAM-regime effect, not L2. Triad 125 GB/s vs seq read 90.7 at 1 GB (+38%, outside the predicted 30%); triad counts 24 B/element including the write, so conventions differ. Flag: stride4 and stride16 at 1 MB report 238 and 202 GB/s line traffic, above the 137 GB/s sequential rate at the same size; not independently validated.

## AI-resilience (E1x)
Naive sequential chase: 0.66 ns to 7.8 ns across all sizes versus 111 ns for the corrected random chase at 1 GB: the prefetcher hides about 93% of DRAM latency. Prediction said "nearly flat"; it was flat above 128 MB but still rose 12x from L1, so "nearly flat" was optimistic. Diagnosis step still to do: disassembly and xctrace evidence (Phase 5).
