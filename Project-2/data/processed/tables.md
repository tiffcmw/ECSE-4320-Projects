Session 20261014-0015; frequency estimate 4.58 GHz.

### Placement check by cache signature (random chase ns; Super: L1D 128 KiB, L2 16 MiB; Performance: L1D 64 KiB, L2 8 MiB)

| QoS class | 48 KiB | 96 KiB | 6 MiB | 12 MiB |
|---|---|---|---|---|
| interactive | 0.66 | 0.66 | 7.97 | 10.60 |
| default | 0.66 | 0.66 | 8.01 | 10.88 |
| background | 2.25 | 14.58 | 45.73 | 126.26 |

### Zero-queue latency (random single-cycle chase, one thread, f = 4.58 GHz estimated)

| Level | Working set | ns, median (IQR) | cycles (est.) | n | Notes |
|---|---|---|---|---|---|
| L1 | 32 KiB | 0.66 (0.65 to 0.66) | 3 | 9 | within 128 KiB Super L1D; 64 KiB Performance L1D would miss here only above 64 KiB |
| L2 | 4 MiB | 7.65 (7.62 to 7.66) | 35 | 9 | within 8 MiB (Performance) and 16 MiB (Super) L2 |
| L2, near capacity | 12 MiB | 10.28 (9.98 to 12.06) | 47 | 9 | fits Super L2 (16 MiB) but not Performance L2 (8 MiB) |
| SLC region | 64 MiB | 89.44 (88.10 to 93.56) | 409 | 9 | beyond L2; SLC size unknown (not exposed), inside the ramp |
| DRAM | 1 GiB | 109.04 (108.98 to 109.18) | 499 | 9 | far beyond any cache; TLB misses included |
| DRAM (loaded harness, 0 BW threads) | 1 GiB | 111.1 | 508 |  | cross-check; separate process, probe thread only |

### Region edges inferred from the latency curve (first working set exceeding 1.5x the plateau; DRAM edge = within 10% of the largest-size value)

| Edge | Working set | sysctl capacity (Super) |
|---|---|---|
| L1 to L2 | 144 KiB | 128 KiB L1D |
| L2 to SLC | 13.4541 MiB | 16 MiB L2 |
| into DRAM plateau | 76.1084 MiB | SLC not exposed |

### Pointer-chase latency per node vs stride (DRAM footprint)

| Test | Order | Stride B | Latency | Implied line rate |
|---|---|---|---|---|
| chase | seq | 64 | 0.9 ns (0.9 to 1.0) | 137.0 GB/s line-rate |
| chase | seq | 128 | 7.8 ns (7.8 to 7.8) | 16.4 GB/s line-rate |
| chase | seq | 256 | 12.0 ns (12.0 to 12.0) | 10.7 GB/s line-rate |
| chase | seq | 512 | 13.5 ns (13.4 to 14.5) | 9.5 GB/s line-rate |
| chase | seq | 1024 | 6.9 ns (6.9 to 6.9) | 18.6 GB/s line-rate |
| chase | seq | 2048 | 103.4 ns (103.4 to 103.5) | 1.2 GB/s line-rate |
| chase | seq | 4096 | 110.4 ns (110.3 to 110.4) | 1.2 GB/s line-rate |
| chase | rand | 64 | 108.2 ns (107.9 to 108.2) | 1.2 GB/s line-rate |
| chase | rand | 128 | 108.7 ns (108.6 to 108.7) | 1.2 GB/s line-rate |
| chase | rand | 256 | 108.7 ns (108.6 to 108.8) | 1.2 GB/s line-rate |
| chase | rand | 512 | 108.4 ns (108.3 to 108.5) | 1.2 GB/s line-rate |
| chase | rand | 1024 | 108.4 ns (108.0 to 108.4) | 1.2 GB/s line-rate |
| chase | rand | 2048 | 110.0 ns (109.3 to 110.9) | 1.2 GB/s line-rate |
| chase | rand | 4096 | 113.4 ns (112.8 to 114.2) | 1.1 GB/s line-rate |

### Independent-load useful bandwidth (GB/s of bytes requested), selected points

| Order | Access B | Stride B | GB/s |
|---|---|---|---|
| seq | 16 | 64 | 27.78 |
| seq | 16 | 128 | 2.86 |
| seq | 16 | 256 | 2.84 |
| seq | 16 | 1024 | 2.87 |
| seq | 64 | 64 | 72.61 |
| seq | 64 | 128 | 17.17 |
| seq | 64 | 256 | 11.32 |
| seq | 64 | 1024 | 11.44 |
| seq | 128 | 128 | 72.46 |
| seq | 128 | 256 | 24.75 |
| seq | 128 | 1024 | 15.64 |
| rand | 16 | 64 | 4.68 |
| rand | 16 | 128 | 2.83 |
| rand | 16 | 256 | 2.88 |
| rand | 16 | 1024 | 3.20 |
| rand | 64 | 64 | 7.01 |
| rand | 64 | 128 | 7.02 |
| rand | 64 | 256 | 7.13 |
| rand | 64 | 1024 | 8.06 |
| rand | 128 | 128 | 7.51 |
| rand | 128 | 256 | 7.59 |
| rand | 128 | 1024 | 8.49 |

### Single-thread mix at 1 GiB footprint: application GB/s and write-allocate-corrected DRAM traffic (model, not measured)

| Mix | application GB/s (IQR) | traffic factor (model) | modeled DRAM GB/s |
|---|---|---|---|
| 100% R | 72.5 (72.3 to 72.6) | 1.00 | 72.5 |
| 70/30 st | 100.5 (99.6 to 100.5) | 1.30 | 130.7 |
| 50/50 st | 114.1 (113.8 to 114.1) | 1.50 | 171.1 |
| 100% W st | 69.2 (69.1 to 69.2) | 2.00 | 138.3 |
| 70/30 stnp | 102.0 (102.0 to 102.4) | 1.00 | 102.0 |
| 50/50 stnp | 129.9 (129.7 to 130.0) | 1.00 | 129.9 |
| 100% W stnp | 144.0 (143.6 to 144.0) | 1.00 | 144.0 |
| 100% W dc zva | 275.1 (275.0 to 275.9) | 1.00 | 275.1 |
| 50/50 rmw | 136.3 (136.2 to 136.6) | 1.00 | 136.3 |

### Loaded latency by mix (probe thread + N bandwidth threads)

| Mix | N threads | app GB/s | probe ns | vs idle |
|---|---|---|---|---|
| 100% R | 4 | 262 | 140 | 1.28x |
| 100% R | 16 | 294 | 196 | 1.79x |
| 70/30 st | 4 | 260 | 161 | 1.47x |
| 70/30 st | 16 | 265 | 192 | 1.76x |
| 50/50 st | 4 | 240 | 177 | 1.62x |
| 50/50 st | 16 | 238 | 210 | 1.91x |
| 100% W st | 4 | 168 | 212 | 1.93x |
| 100% W st | 16 | 177 | 1032 | 9.43x |
| 100% W stnp | 4 | 208 | 153 | 1.39x |
| 100% W stnp | 16 | 230 | 336 | 3.06x |
| 100% W dc zva | 4 | 313 | 170 | 1.55x |
| 100% W dc zva | 16 | 311 | 188 | 1.71x |
| 50/50 rmw | 4 | 338 | 192 | 1.76x |
| 50/50 rmw | 16 | 379 | 245 | 2.24x |

### Knee and Little's Law: lines in flight N = BW x latency / 128 B (idle latency 111 ns)

| Point | bandwidth | loaded latency | N (lines in flight) | config |
|---|---|---|---|---|
| highest BW with latency <= 1.5x idle | 301 GB/s | 150 ns | 354 | delay, 6 thr N=6, delay=0 |
| max BW / latency (power) point | 295 GB/s | 143 ns | 329 | threads N=5, delay=0 |
| maximum measured BW | 301 GB/s (66% of 460) | 150 ns | 354 | delay, 6 thr N=6, delay=0 |

### Single-core concurrency sweep: N_eff = throughput x L0 / 128 B with L0 = 109 ns (K = 1 latency)

| K chains | GB/s | ns per step | N_eff (lines) |
|---|---|---|---|
| 1 | 1.2 | 109 | 1.0 |
| 2 | 2.3 | 109 | 2.0 |
| 3 | 3.5 | 109 | 3.0 |
| 4 | 4.7 | 109 | 4.0 |
| 6 | 7.0 | 110 | 6.0 |
| 8 | 9.3 | 111 | 7.9 |
| 12 | 13.7 | 112 | 11.7 |
| 16 | 18.0 | 114 | 15.4 |
| 20 | 21.5 | 119 | 18.4 |
| 24 | 21.9 | 141 | 18.7 |
| 32 | 22.0 | 186 | 18.8 |
| 40 | 22.0 | 233 | 18.8 |
| 48 | 22.0 | 279 | 18.8 |
| 64 | 22.1 | 371 | 18.8 |

### All loaded-latency points (median over rounds)

| series | BW threads | delay iters | GB/s | latency ns | N lines |
|---|---|---|---|---|---|
| delay, 6 thr | 6 | 3200000 | 8.0 | 126 | 8 |
| delay, 6 thr | 6 | 1600000 | 15.8 | 126 | 16 |
| delay, 16 thr | 16 | 3200000 | 20.5 | 134 | 22 |
| delay, 6 thr | 6 | 800000 | 30.4 | 121 | 29 |
| delay, 16 thr | 16 | 1600000 | 39.9 | 137 | 43 |
| delay, 6 thr | 6 | 400000 | 56.0 | 123 | 54 |
| threads | 1 | 0 | 68.7 | 120 | 64 |
| delay, 16 thr | 16 | 800000 | 76.4 | 137 | 82 |
| delay, 6 thr | 6 | 200000 | 96.3 | 127 | 95 |
| threads | 2 | 0 | 135.9 | 129 | 137 |
| delay, 16 thr | 16 | 400000 | 138.5 | 149 | 161 |
| delay, 6 thr | 6 | 100000 | 154.6 | 131 | 159 |
| delay, 6 thr | 6 | 60000 | 199.5 | 136 | 213 |
| threads | 3 | 0 | 204.3 | 127 | 202 |
| delay, 16 thr | 16 | 200000 | 217.4 | 170 | 289 |
| threads | 4 | 0 | 262.0 | 138 | 283 |
| delay, 6 thr | 6 | 20000 | 269.0 | 139 | 293 |
| delay, 16 thr | 16 | 100000 | 282.6 | 176 | 388 |
| threads | 12 | 0 | 288.7 | 171 | 386 |
| threads | 10 | 0 | 290.7 | 154 | 350 |
| threads | 16 | 0 | 294.0 | 192 | 442 |
| threads | 5 | 0 | 294.6 | 143 | 329 |
| threads | 14 | 0 | 295.0 | 186 | 428 |
| delay, 16 thr | 16 | 60000 | 295.1 | 183 | 421 |
| delay, 16 thr | 16 | 0 | 295.3 | 188 | 433 |
| delay, 16 thr | 16 | 20000 | 296.6 | 188 | 436 |
| threads | 6 | 0 | 301.2 | 151 | 356 |
| threads | 8 | 0 | 301.4 | 153 | 359 |
| delay, 6 thr | 6 | 0 | 301.5 | 150 | 354 |

### Kernel cost: smallest vs largest footprint and AMAT-style prediction (hit time + miss ratio x (L(F) - L_L1) / N, N = 19 lines from Exp 4)

| Kernel | Pattern | ns/elem smallest | ns/elem largest | ratio | AMAT pred. largest ns | measured/pred. |
|---|---|---|---|---|---|---|
| mul | unit | 0.042 | 0.121 | 2.9x | 0.223 | 0.54 |
| mul | stride 64 B | 0.243 | 1.722 | 7.1x | 3.138 | 0.55 |
| mul | scattered | 0.229 | 10.545 | 46.0x | 6.019 | 1.75 |
| saxpy | unit | 0.044 | 0.079 | 1.8x | 0.223 | 0.35 |
| saxpy | stride 64 B | 0.249 | 1.227 | 4.9x | 3.127 | 0.39 |
| saxpy | scattered | 0.231 | 6.896 | 29.8x | 5.986 | 1.15 |

### TLB experiment: latency with one line per page vs the same number of lines packed (median ns)

| pages touched | paged | packed | difference |
|---|---|---|---|
| 8 | 0.12 | 0.12 | -0.00 |
| 16 | 0.66 | 0.66 | +0.00 |
| 32 | 0.66 | 0.65 | +0.00 |
| 64 | 0.65 | 0.66 | -0.00 |
| 128 | 0.66 | 0.66 | +0.00 |
| 256 | 1.97 | 0.66 | +1.32 |
| 512 | 1.97 | 0.66 | +1.31 |
| 1024 | 1.98 | 0.66 | +1.32 |
| 2048 | 7.59 | 2.58 | +5.01 |
| 4096 | 12.05 | 2.62 | +9.43 |
| 8192 | 12.51 | 2.74 | +9.77 |
| 16384 | 13.15 | 7.12 | +6.02 |
| 32768 | 18.56 | 7.62 | +10.94 |
| 65536 | 30.99 | 8.13 | +22.86 |

### Fixed 4 MiB of lines spread over P pages (median ns)

| P pages | ns |
|---|---|
| 256 | 7.64 |
| 512 | 8.10 |
| 1024 | 12.89 |
| 2048 | 22.76 |
| 4096 | 32.98 |
| 8192 | 39.64 |
| 16384 | 25.12 |
| 32768 | 18.78 |

### Pitfall 1: aggregate 'bandwidth' by total footprint (16 threads)

| total footprint | GB/s |
|---|---|
| 4 MiB | 1085 (1085 to 1086) |
| 16 MiB | 1094 (1093 to 1094) |
| 64 MiB | 357 (357 to 357) |
| 256 MiB | 298 (297 to 298) |
| 1 GiB | 295 (294 to 296) |
| 4 GiB | 296 (254 to 297) |

### Pitfall 4: clock estimate after 3 s idle vs steady (4.58 GHz)

| ms since burst start | GHz estimate | fraction of steady |
|---|---|---|
| 0 | 1.34 | 0.29 |
| 5 | 2.28 | 0.50 |
| 10 | 2.55 | 0.56 |
| 20 | 3.16 | 0.69 |
| 50 | 3.98 | 0.87 |
| 100 | 4.58 | 1.00 |
| 150 | 4.58 | 1.00 |
