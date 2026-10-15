# Appendix A. Code map

| File (Project-2 folder) | Purpose |
|---|---|
| `src/membench.c` | All benchmark kernels and sub-commands: chase, tlb, bw, pat, mlp, loaded, kern, dce, ramp, mut, hugetest, selftest |
| `src/common.h` | Timer, page-aligned mapping, QoS helpers, argument parsing, long-format CSV output |
| `src/pmu.h` | Optional PMU access through the private kperf frameworks (needs root) |
| `scripts/build.sh` | Compiles with the flags listed in Table 2 |
| `scripts/run_exp.py` | Experiment definitions; shuffled rounds; machine-readable metadata per run |
| `scripts/meta.py` | Hardware, OS, compiler, power, thermal and policy metadata |
| `scripts/parse.py`, `scripts/validate.py` | Median, min, max, n per configuration; sanity checks |
| `scripts/plot.py`, `scripts/analysis_lib.py` | Figures and tables |
| `scripts/build_report.py`, `scripts/check_report.py` | Assemble this report from the data; recompute its numbers from the raw files |
| `scripts/run_privileged.sh` | powermetrics and PMU counter run (needs sudo) |

# Appendix B. Deviations from the assignment

| Assignment asks for | What was done instead | Consequence |
|---|---|---|
| Intel Memory Latency Checker | Own benchmarks: random-cycle pointer chase, NEON streaming kernels, loaded-latency harness (probe chase thread plus N bandwidth threads with adjustable injection delay) | Absolute numbers are not comparable to MLC output; the method is described in Section 1.1 |
| `perf` cache and TLB miss counters | Counters through Apple's private `kperf` interface need administrator rights. See Appendix H for the attempts and outcome | {{counters_deviation()}} |
| Thread pinning, governor, SMT off | Not available on macOS (no `taskset`, no governor, no SMT on this chip). QoS class set per thread; DVFS left automatic and recorded | Placement is inferred, not guaranteed; frequency is estimated, not fixed |
| Huge-page comparison | Not possible: `mach_vm_allocate` with `VM_FLAGS_SUPERPAGE_SIZE_2MB` and `_ANY`, and `mmap` with the superpage flag, all fail with "invalid argument" | TLB effects are shown through page locality only (Section 8) |
| L3 cache | The chip has a system-level cache whose size `sysctl` does not report | Shown as a latency ramp between L2 and DRAM; no capacity is claimed |
| Frequency in cycles | Cycles are ns times an estimated clock | Every cycle value is labeled an estimate |
| NUMA | Unified memory, no NUMA | not applicable |

: Table 3. Deviations from the assignment.

**Reproduction.**

From the Project-2 folder: `scripts/run_all.sh` rebuilds the program, runs the self-test, parses the stored raw data, validates and plots. `COLLECT=full scripts/run_all.sh` re-measures everything (about 30 minutes on a quiet machine, AC power). `sudo scripts/run_privileged.sh` adds the counter run and the powermetrics check.

# Appendix C. Hypotheses, measured results and verdicts

Predictions were written before the benchmarks existed (the first group, H1a to H8d) or before the corresponding new measurements were read (the second group, H7d to H13, Appendix D). Text is reproduced without change except that bracketed references to numbers from an earlier, separate pointer-chase exercise on the same machine were removed. Those numbers informed some of the predictions (L1, L2 and DRAM latency, the 2.6 ns step, the sequential-chase ratio, one-core read bandwidth, TLB onset and penalty), so those predictions were not blind.

{{hyp_table()}}

: Table 18. Predictions and verdicts. HV1 to HV3 are validity checks. "Partly" means that part of the prediction held.

# Appendix D. Hypotheses amended after seeing data

The original predictions stay visible in Table 18. The table lists every hypothesis whose wording, design or evaluation changed after data were seen, and every prediction added after a first look at results.

| ID | Original text | Amended text | Reason |
|---|---|---|---|
| H2b | Random chase latency does not depend on node stride once the footprint is fixed at 1 GiB | Footprint is the larger of 1 GiB and 1 Mi lines times the stride (1 Mi distinct lines at every stride) | Holding the byte footprint fixed shrank the number of distinct lines at large strides and made them cache resident (29 ns instead of 109 ns at 16 KiB) |
| H2c | At 16 KiB stride a sequential chase is still at least 2x faster than random | Evaluated only for strides up to 4 KiB; 16 KiB dropped | The 1 Mi-line design would need 16 GiB at 16 KiB stride |
| H2d, H3a, H3b, H3c, H5a | Evaluated on the first collection | Evaluated only on data collected after the read-kernel dependency chain was removed | The first read kernels were capped at 73 GB/s at every footprint (Section 13) |
| H3b, H3c | `dc zva` and `stnp` advantages interpreted as evidence of write-allocate traffic | Interpretation withdrawn; random-data variants are the reference and zero and uniform variants are a separate content test (H3e) | Zero and uniform lines run 2 to 4 times faster than random lines (Table 8) |
| H4c, H4d (idle latency) | Probe idle latency taken as about 109 ns | Probe warm-up changed from sleeping to spinning | The probe slept and lowered its own clock (119 ns instead of 109 ns) |
| H7a, H7b | Penalty defined as one line per page minus the same lines packed | Penalty defined as random in-page offsets minus packed | The original placement mixed cache-set conflicts with translation cost |
| Exp 7 design | Sweep from one page | Sweep from 2 pages | A cycle of 8 nodes reads 0.12 ns, below L1 latency |
| HV3, H4b (peak) | 460 GB/s from secondary sources | 460 GB/s from Apple's specification for the 32-core-GPU configuration | Source checked; no percentage changed |
| H7d, H2f, H3e, H4f, H11, H12, H9, H13 | not present | Added with predictions written before the new measurements were read | New tests added to separate confounds (TLB placement, stride aliasing, content dependence, knee definitions, read ceiling, plateau, clock, counters). A few single-run smoke tests were seen first and are disclosed in the prediction text |
| H4f (K1 implementation) | K1 = lowest-load point reaching 95% of maximum | Unchanged definition; first implementation ordered points by bandwidth (selected 10 threads) and was corrected to first crossing along the thread sweep (5 threads) | Implementation error found when the result disagreed with the thread table |

: Table 19. Amendments.

# Appendix E. Code excerpts

**Pointer chase** (one random cycle through all nodes; every load depends on the previous one):

{{code_excerpt('chase', r'^static void chase_link', r'^static __attribute__\(\(noinline\)\) void \*chase_loop', maxlines=7)}}
{{code_excerpt('chase2', r'^static __attribute__\(\(noinline\)\) void \*chase_loop', r'^}', maxlines=8)}}

**Streaming bandwidth kernel** (independent accumulators; the sum is returned and sunk):

{{code_excerpt('rd', r'^static inline uint32x4_t rd_line', r'^}', maxlines=8)}}
{{code_excerpt('mix', r'^#define DEF_MIX', r'^    }$', maxlines=12)}}

**Loaded-latency harness** (bandwidth threads stream while the probe thread chases; per-thread byte counters give bandwidth):

{{code_excerpt('bwt', r'^static void \*bw_thread', r'^}', maxlines=14)}}
{{code_excerpt('probe', r'warm_spin\(200\)', r'emit\(exp, m->name, bufsz, 0, LINE, N, dl, r, "bw_gbps", tot\)', maxlines=12)}}

**QoS setup** (each worker sets the class on itself; the class is read back and stored with every result row):

{{code_excerpt('qos', r'^static inline int qos_from_name', r'^static inline int get_thread_qos', path='src/common.h', maxlines=12)}}

**Dead-code evidence.** The unused-result read loop has no symbol in the binary and the timing function calls only the sinking variant:

{{dce_evidence()}}

