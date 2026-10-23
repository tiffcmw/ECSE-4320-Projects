# 10. AMAT and Little's Law synthesis

Average memory access time for a dependent load stream is the hit-weighted sum of the level latencies of Section 2: {{v['L1']|.2f}} ns (L1), about {{v['L2_2M']|.1f}} ns (L2), {{v['SLC64']|.0f}} ns in the system-level-cache ramp at 64 MiB and {{v['DRAM']|.0f}} ns (DRAM) *(measured)*. For independent accesses the average cost per access divides the miss penalty by the number of misses in flight, which is Little's Law, N = bandwidth times latency divided by the line size:

| Case | Latency | Lines in flight N | Bandwidth = N x 128 B / latency | Source |
|---|---|---|---|---|
| One core, random demand misses | {{v['L0']|.0f}} ns | {{v['Ncore']|.1f}} | {{v['mlp_plateau']|.1f}} GB/s | Exp 4a; N is known by construction up to the plateau |
| One core, sequential stream | {{v['lat1']|.0f}} ns | {{v['bw1']*v['lat1']/128|.0f}} (inferred) | {{v['bw1']|.0f}} GB/s | Exp 4b; prefetcher raises N |
| Chip at the knee (5 threads) | {{v['lat5']|.0f}} ns | {{v['bw5']*v['lat5']/128|.0f}} (inferred) | {{v['bw5']|.0f}} GB/s | Exp 4b |
| Chip, 16 threads | {{v['lat16']|.0f}} ns | {{v['bw16']*v['lat16']/128|.0f}} (inferred) | {{v['bw16']|.0f}} GB/s | Exp 4b; flat bandwidth, longer queue |

: Table 17. Little's Law across the experiments. For rows marked inferred N is computed from the measured bandwidth and latency; no independent count of in-flight requests is available.

The AMAT-style model of Exp 6 (Table 14) reproduces the scattered kernel within a factor of {{v['am_mul_scattered']|.1f}} using only the measured latency curve and the one-core concurrency of {{v['Ncore']|.0f}} lines, and over-predicts the unit-stride cost where the prefetcher raises the concurrency far above that value. The picture that fits all experiments *(inferred)*: latency is set by the level that serves the load; one core's throughput is its number of outstanding misses divided by that latency (about {{v['Ncore']|.0f}} for demand misses, many more with prefetching); the chip's throughput saturates near {{v['maxbw']|.0f}} GB/s with 5 to 6 streaming cores, after which extra requests only lengthen the queue and the latency; and which internal limit sets that plateau is not determined.

# 11. Anomalies and unresolved items

**Tested, and the test narrowed the explanation**

1. *Read-only ceiling.* Streaming reads saturate at {{v['maxbw']|.0f}} GB/s ({{pk(v['maxbw'])|.0f}}% of peak) while read-modify-write reaches {{v['rmw16']|.0f}} GB/s and read plus `stnp` writer threads move 355 GB/s in total. Excluded by test: the load instruction mix, the buffer content, the DRAM peak. Not excluded and untested: limits on read-return bandwidth, on outstanding requests, or QoS-related throttling (background threads reach only 46 GB/s). Cause: unknown.
2. *The 2.6 ns plateau between L1 and L2.* Follows bytes, not node count (a node-count predictor is excluded). Its identity is not established; the non-repeating-walk test was inconclusive.
3. *Slow strides.* The penalty at 128, 256, 384, 512, 640 and 1024 B strides follows multiples of the 128 B line, not powers of two; a hashed offset does not remove it. Why 192 B and 320 B strides are faster is untested.
4. *Content-dependent stores.* Zero lines and uniform lines are written faster than random lines. The mechanism (detection of uniform lines, compression, write combining) is untested.
5. *TLB placement artifact.* Explained: the original placement mapped lines to a conflicting set of cache sets in the fixed-footprint panel; random offsets remove it.

**Unexplained and untested**

6. Random 128 B independent loads deliver about a third of the line traffic of random 16 B loads ({{v['pat_rand_128_128']|.1f}} GB/s against {{v['pat_rand_16_128']*8|.1f}} GB/s of line-equivalent traffic) in the same kernel.
7. The sequential chase is faster at a 1 KiB stride ({{v['seq1024']|.1f}} ns) than at 256 B and 512 B ({{v['seq256']|.1f}} and {{v['seq512']|.1f}} ns).
8. The latency ramp toward the system-level cache begins at {{v['edgeL2']/2**20|.1f}} MiB, below the 16 MiB capacity.
9. Small non-monotonic wiggles in the TLB penalty (up to 1.6 ns) and a cycle of exactly 8 nodes that reads 0.12 ns per load, below the L1 latency (the loop unroll repeats the same 8 addresses; excluded from all results as degenerate).
10. The probe latency at 16 threads occasionally shows rounds of tens of microseconds (visible as the upper bars of Figure 4d), and the 70/30 plain-store mix at 16 threads has a median probe latency of {{g('e3_mix_loaded','lat_ns',variant='r7w3_st_r',threads=16)|.0f}} ns. Background activity cannot be excluded; medians are reported.
11. Which cores run the bandwidth threads above 6 threads cannot be observed.

# 12. Limitations

* **No hardware counters in the main dataset** (Section 1.3, Appendix H). Every cache and TLB statement is inferred from timing.
* **The clock is estimated** from a dependent-add chain assuming one cycle per add. {{powermetrics_text()}}
* **The peak, 460 GB/s, is a specification**, not a measurement; the validation flags only values above it.
* **No pinning.** Threads run at user-interactive QoS; the Super-core signature is verified for the first thread only.
* **No huge pages**, no SLC capacity, no fixed frequency.
* **Single machine, single operating-system image, battery power** for the main collection (an earlier AC collection agreed within 1%). Background daemons were active for a few percent of one core; the medians over 5 to 12 rounds absorb them, the minimum-to-maximum ranges show them.
* **Rounds:** n is 12 for the headline experiments and 5 to 9 elsewhere; with n below 10 only minimum-to-maximum ranges are shown.
* **The AMAT model** uses assumed miss ratios (no counters).

# 13. Benchmark flaws found and fixed

Each flaw was found by inspecting a result that looked implausible; the code was corrected and the dependent data re-collected.

1. **Dependency chain in the read kernels.** One XOR accumulator capped one-thread read bandwidth at about 73 GB/s at every footprint. Independent accumulators removed it (now {{v['bw1G']|.0f}} GB/s at 1 GiB, {{v['bw32K']|.0f}} GB/s at 32 KiB).
2. **Stride sweeps shrank the cache footprint.** A fixed byte footprint reduced the distinct lines at large strides (a random chase at 16 KiB stride read 29 ns instead of about 109 ns). The sweeps now hold 1 Mi distinct lines.
3. **The latency probe lowered its own clock** by sleeping 200 ms before measuring (idle 119 ns against 109 ns). It now spins.
4. **The injection-delay range was too weak** to reach low loads; it now reaches 3.2 million loop iterations.
5. **A degenerate 8-node cycle** read 0.12 ns per load, below the L1 latency; the sweep starts at 2 pages and the point is excluded.
6. **Store kernels wrote uniform lines**, which made `stnp` and `dc zva` look twice as fast as plain stores. With random data the `stnp` advantage is {{100*(v['mix_r0w10_nt_r']/v['mix_r0w10_st_r']-1)|.0f}}%. Zero and uniform variants are kept as a labeled test (Table 8).
7. **The TLB layout mixed cache-set conflicts with translation cost** (Section 8); random offsets and a constant-offset control separate them.
8. **The knee was first computed by ordering points by bandwidth**, which selected 10 threads on this noisy curve. The definition as written (first crossing along the thread sweep) selects 5 and is reported.
9. **Numbers typed into text by hand disagreed with the data tables in places.** All numbers here are generated from the processed data by a script and recomputed from the raw files by a second script.
