# Defense sheet (private team notes, not part of the submission)

Numbers are from the final collection and are generated in the report; check them against the report tables before answering. Answers are two sentences each. "Weakest claims" at the end lists where a grader can push hardest.

## Exp 1: zero-queue baselines
1. **Why a random permuted single cycle?** Every load depends on the previous one, so nothing can overlap, and a random single cycle gives the prefetcher no pattern; a sequential chase reads 7.8 ns per node against 108 ns for the random one (Exp 8).
2. **Why is the L2 value taken at 2 MiB, not 4 MiB?** The 4 MiB footprint spans 256 pages and the TLB experiment shows about 1.3 ns of translation cost from 256 pages, so 2 MiB (7.1 ns, 33 cycles estimated) is the cleaner L2 figure.
3. **How do you know a thread ran on a Super core?** The latency steps sit at the Super capacities (L1D 128 KiB, L2 16 MiB) for user-interactive threads, while background-QoS threads show the Performance signature (96 KiB already misses L1); this is verified for the first thread only, not above 6 threads.

## Exp 2: pattern and granularity
1. **Why hold 1 Mi distinct lines at every stride?** A fixed byte footprint shrinks the number of distinct lines as the stride grows, so large strides become cache resident and read 29 ns instead of 109 ns; holding the line count constant keeps the footprint far beyond the cache.
2. **Why does the prefetch benefit end near 1 KiB?** The sequential chase is fast up to a 1 KiB stride (6.8 ns) and not at 2 KiB (103 ns); that the prefetcher stops tracking larger strides is an inference, and the 1 KiB value being faster than 256 and 512 B is unexplained.
3. **Is the 128/256 B stride penalty power-of-two aliasing?** No: 384 B and 640 B are as slow as 128 B while 192 B and 320 B are 1.6 times faster, and a hashed offset does not change the power-of-two strides; the penalty follows multiples of the 128 B line, cause untested.

## Exp 3: read/write mix
1. **Why random data for the stores?** Plain stores of zero lines run at 277 GB/s and `stnp` of uniform lines at 142 GB/s against 68 and 91 GB/s for random lines, so uniform or zero data measures a different (cheaper) path; random data is the honest reference.
2. **Is write-allocate shown?** No. The direct test (`dc zva`) equals zero-data stores, so it is confounded by content, and `stnp` with random data is only 33% faster than plain stores, not the factor of about 2 that skipping an allocate fetch would give; the 2x traffic column in the table is a model.
3. **Why is mixed traffic faster than read-only for one core?** One core's read rate is limited by outstanding demand misses (about 19) or by what its prefetcher sustains, while stores drain through a separate path; this is consistent with read-modify-write being fastest (137 GB/s) but is not proven.

## Exp 4: intensity, knee, Little's Law
1. **What does N = 19 mean and how was it derived?** One thread with K independent random chains reaches a plateau of 21.9 GB/s; N = throughput times the single-chain latency (110 ns) divided by 128 B is 18.9 lines, and for K up to 20 it equals K exactly, which validates the method where the true count is known.
2. **Why two knee definitions?** K1 (first thread count at 95% of the maximum, 5 threads) and K2 (maximum bandwidth over latency, 4 threads) differ by one thread, so the conclusion (knee at 4 to 5 threads, latency 1.26 to 1.32 times idle) does not hinge on one rule; the definitions were fixed in writing before the analysis, after having seen an earlier version of the curve.
3. **Why is 293 GB/s only 64% of 460 GB/s?** Nobody knows from these data: instruction mix, buffer content and the DRAM peak were excluded by test (read-modify-write reaches 374 GB/s, read plus `stnp` writers 355 GB/s total), but the limiting component is not identified.

## Exp 5: working-set sweep and plateau
1. **How are the level edges chosen?** The first footprint above 1.5 times the plateau latency (L1 edge 144 KiB), the start of the ramp (13.5 MiB) and the point within 10% of the DRAM value (76 MiB); no SLC capacity is claimed because the latency rises smoothly.
2. **What is the 2.6 ns plateau?** An unexplained level between L1 and L2 that follows capacity in bytes (the same edge for 64, 128 and 256 B node spacing) and not node count, which excludes a node-count predictor; the non-repeating-walk test was inconclusive.
3. **Why does the one-core L1 bandwidth (211 GB/s) not exceed 300 GB/s?** The prediction was wrong; the kernel issues 16-byte loads and the measured value is what one core delivered, with independent accumulators so the chain is not the limit.

## Exp 6: kernels and AMAT
1. **Why is the unit-stride rise only 3x or less?** The prefetcher hides the latency for unit stride, so the AMAT model, which assumes demand misses, over-predicts the cost by 1.8 to 2.9 times for unit stride.
2. **Where does the scattered ratio come from?** It is the scattered cost divided by the unit-stride cost at the same footprint: 5.4x at 12 KiB, 16x at 6 MiB, 88x at 1.5 GiB; any single ratio needs its footprint.
3. **How are misses known without counters?** They are not measured: miss ratios in the model come from the footprint and the line size (1/32 per element for unit stride), and the counter attempt is logged in Appendix H.

## Exp 7: TLB
1. **Why is the penalty paged with random offsets minus packed?** The original placement put lines at offsets that created cache-set conflicts in some panels; random offsets remove them, and a constant-offset control shows how large the conflict effect can be (about 90 ns).
2. **What changed after the fix?** The penalty at 65536 pages is 7 ns, not 16 ns, and the fall in the fixed-footprint panel was an artifact; the onset at 256 pages (+1.3 ns) is unchanged.
3. **Why no huge pages?** `mach_vm_allocate` with the superpage flags and `mmap` with the superpage flag all fail with "invalid argument" on this system, so no claim about huge pages is made.

## Exp 8: pitfalls
1. **Why does a 4 MiB buffer give 1852 GB/s?** It is resident in the shared L2 across the 16 threads, so it measures cache bandwidth, not DRAM, and exceeds the 460 GB/s peak, which the validation flags.
2. **How do you know the optimizer deleted the loop?** The function has no symbol in the binary and the caller only calls the sinking variant (Appendix E); timing it claims 1.2e9 GB/s.
3. **Why a 300 ms spin before every measurement?** A process after idle runs at 43% of the steady clock after 5 ms and reaches the steady value after about 100 ms.

## Five weakest claims and what would strengthen them
1. **No hardware counters (main dataset).** All cache and TLB attributions are timing inference. Strengthen: run `sudo scripts/run_privileged.sh` and report the counters for Exp 6 and 7; or Instruments with custom events through its window.
2. **The frequency is an estimate** (dependent adds, one cycle assumed). Strengthen: powermetrics cross-check from the same privileged script.
3. **The read-only ceiling at 64% of peak is unexplained.** Strengthen: tests that vary the number of prefetch streams per thread, the access size per stream, and the number of cores per cluster, plus counters of outstanding requests.
4. **The plateau between L1 and L2 and the half-line-stride speed-up are unexplained.** Strengthen: a victim-cache or sector test (access patterns that alternate between two sets of lines) and a test of offsets of 64 B inside the line.
5. **Write-allocate is not established, and the mechanism behind zero and uniform lines is untested.** Strengthen: data with the same entropy but different structure (alternating zero and random lines, random lines with a repeated 16 B pattern), and DRAM-side counters.
