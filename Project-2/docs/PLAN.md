# Plan

One C harness (`src/membench.c`) with subcommands; Python drives experiments in shuffled order, writes one raw CSV per experiment, then `parse.py` produces processed tables (median, IQR, min, max, n) and `plot.py` the figures.

| Exp | Subcommand | Sweep |
|---|---|---|
| 1 zero-queue | `chase` random, small to 2 GiB | levels L1, L2, SLC, DRAM; ns and cycles at measured f |
| 2 pattern and granularity | `chase` seq/random x stride, `bw` strided/random | strides 64, 128, 256, 512, 1024, 4096, 16384 B; access sizes 16 to 128 B |
| 3 read/write mix | `bw` mix, `loaded` | 100R, 70/30, 50/50, 100W; temporal vs non-temporal (stnp) vs `dc zva` |
| 4 intensity | `mlp`, `loaded` | chains 1..48 in one thread; BW threads 0..17 and injection delay |
| 5 working set | `chase` + `bw` read | 4 KiB to 2 GiB, annotated by level |
| 6 cache-miss impact | `kern` | z=x*y, y=a*x+y; footprint x {seq, stride, random}; correctness vs reference |
| 7 TLB | `tlb` | pages touched 1 to 65536, one line per page vs packed, same cache footprint |
| 8 pitfalls | `chase`, `bw`, `pitfall` | cache-resident "DRAM", prefetchable chase, dead-code elimination, frequency ramp |

Repetitions: full mode 9 to 15 per point, quick mode 3. Warmup excluded. Timed regions at least 10 ms (24 MHz clock).
