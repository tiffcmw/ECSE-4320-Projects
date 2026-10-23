# Appendix G. Team contribution statement

Names are placeholders. Each member owns the listed experiments and report sections and can explain every number in them from the raw data.

| Member | Experiments and review items | Report sections |
|---|---|---|
| Tiffany Cheng, latency and locality | Exp 1, Exp 2 (including stride aliasing), Exp 5 (including plateau tests), core placement, frequency cross-check | 2, 3, 6 |
| Marie Morales, bandwidth and concurrency | Exp 3 (including content test), Exp 4 (loaded latency, knee, Little's Law, read-ceiling tests), peak bandwidth | 4, 5 |
| Alex Redd, misses, TLB and pitfalls | Exp 6, Exp 7 (including layout controls and the huge-page attempt), Exp 8, counters attempt | 7, 8, 9 |
| Shared | Hypothesis amendments (each member for their own experiments), rounds and statistics, limitations, proofreading, AI-use note | 1, 10 to 13, Appendices |
| Claude Code | Benchmark and plotting code and fixes, approved re-collection, the numeric consistency check, figure regeneration, report assembly. It proposes verdicts with the evidence; the owning member confirms each verdict. | all (drafting) |

Cross-review: Tiffany Cheng reviews Marie Morales's experiments, Marie Morales reviews Alex Redd's, Alex Redd reviews Tiffany Cheng's. Each reviewer reproduces one headline number from the raw data with the provided scripts. [STUDENT TO FILL: reviewer, number reproduced, date, for each pair]

# Appendix H. Hardware-counter attempts

{{counters_appendix()}}

# Appendix I. Additional tables

{{kern_table()}}

: Table 13. Kernel cost at the smallest, a middle and the largest footprint (median ns per element, n = 5). The scattered-to-unit ratio depends on the footprint.


{{T('Pointer-chase latency per node')}}

: Table 5. Pointer-chase latency per node versus stride (1 Mi distinct lines). "Implied line rate" is 128 B divided by the latency.

{{T('Independent random 16 B loads')}}

: Table 6. Independent random 16 B loads by stride, with and without a hashed line offset in the stride block.

{{delay_table()}}

: Table 10. Injection-delay series (median of 12 rounds). The delay series trace the throughput-latency curve below saturation.

{{T('Read ceiling tests')}}

: Table 11. Aggregate read GB/s by thread count and variant (median).

{{T('Read plus concurrent writer threads')}}

: Table 12. Readers plus two concurrent writer threads.

{{fixedL_table()}}

: Table 16. A fixed 4 MiB of lines spread over P pages (median ns, n = 12).


{{T('Plateau tests')}}

: Table 20. Plateau tests: median ns per load by footprint and node spacing, and the mutating walk.

{{T('Kernels: ns per element by element stride')}}

: Table 21. Kernel ns per element by element stride at the two largest footprints, plain and hashed offset (n = 7).

{{T('Independent-load useful bandwidth')}}

: Table 22. Independent-load useful bandwidth (GB/s), selected points (n = 9).

{{T('Loaded latency by mix')}}

: Table 23. Loaded latency by mix.

{{T('Fixed 4 MiB')}}

: Table 24. Fixed 4 MiB of lines over P pages (also Table 16).
