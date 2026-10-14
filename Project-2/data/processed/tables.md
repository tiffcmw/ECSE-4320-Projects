Session 20261014-0003; frequency estimate 4.58 GHz.

### Placement check by cache signature (random chase ns; Super: L1D 128 KiB, L2 16 MiB; Performance: L1D 64 KiB, L2 8 MiB)

| QoS class | 48 KiB | 96 KiB | 6 MiB | 12 MiB |
|---|---|---|---|---|
| interactive | 0.66 | 0.66 | 7.95 | 9.39 |
| default | 0.66 | 0.66 | 7.92 | 11.39 |
| background | 2.14 | 14.70 | 44.97 | 127.91 |

### Zero-queue latency (random single-cycle chase, one thread, f = 4.58 GHz estimated)

| Level | Working set | ns, median (IQR) | cycles (est.) | n | Notes |
|---|---|---|---|---|---|
| L1 | 32 KiB | 0.66 (0.66 to 0.66) | 3 | 9 | within 128 KiB Super L1D; 64 KiB Performance L1D would miss here only above 64 KiB |
| L2 | 4 MiB | 7.62 (7.62 to 7.65) | 35 | 9 | within 8 MiB (Performance) and 16 MiB (Super) L2 |
| L2, near capacity | 12 MiB | 11.54 (10.35 to 11.74) | 53 | 9 | fits Super L2 (16 MiB) but not Performance L2 (8 MiB) |
| SLC region | 64 MiB | 90.57 (88.12 to 96.87) | 414 | 9 | beyond L2; SLC size unknown (not exposed), inside the ramp |
| DRAM | 1 GiB | 109.09 (109.02 to 109.42) | 499 | 9 | far beyond any cache; TLB misses included |
| DRAM (loaded harness, 0 BW threads) | 1 GiB | 119.5 | 547 |  | cross-check; separate process, probe thread only |

### Region edges inferred from the latency curve (first working set exceeding 1.5x the plateau; DRAM edge = within 10% of the largest-size value)

| Edge | Working set | sysctl capacity (Super) |
|---|---|---|
| L1 to L2 | 144 KiB | 128 KiB L1D |
| L2 to SLC | 12 MiB | 16 MiB L2 |
| into DRAM plateau | 76.1084 MiB | SLC not exposed |

### Pointer-chase latency per node vs stride (DRAM footprint)

| Test | Order | Stride B | Latency | Implied line rate |
|---|---|---|---|---|
| chase | seq | 64 | 1.4 ns (1.3 to 1.4) | 93.0 GB/s line-rate |
| chase | seq | 128 | 7.8 ns (7.8 to 7.9) | 16.3 GB/s line-rate |
| chase | seq | 256 | 12.0 ns (12.0 to 12.0) | 10.6 GB/s line-rate |
| chase | seq | 512 | 14.5 ns (14.4 to 14.9) | 8.8 GB/s line-rate |
| chase | seq | 1024 | 6.8 ns (6.8 to 6.9) | 18.7 GB/s line-rate |
| chase | seq | 4096 | 104.9 ns (104.5 to 106.5) | 1.2 GB/s line-rate |
| chase | seq | 16384 | 36.8 ns (29.4 to 41.8) | 3.5 GB/s line-rate |
| chase | rand | 64 | 108.4 ns (108.2 to 108.6) | 1.2 GB/s line-rate |
| chase | rand | 128 | 109.1 ns (108.8 to 109.2) | 1.2 GB/s line-rate |
| chase | rand | 256 | 108.8 ns (108.8 to 109.6) | 1.2 GB/s line-rate |
| chase | rand | 512 | 108.1 ns (108.0 to 108.8) | 1.2 GB/s line-rate |
| chase | rand | 1024 | 107.9 ns (107.9 to 108.3) | 1.2 GB/s line-rate |
| chase | rand | 4096 | 102.2 ns (100.4 to 104.1) | 1.3 GB/s line-rate |
| chase | rand | 16384 | 29.4 ns (25.7 to 32.2) | 4.4 GB/s line-rate |

### Independent-load useful bandwidth (GB/s of bytes requested), selected points

| Order | Access B | Stride B | GB/s |
|---|---|---|---|
| seq | 16 | 64 | 27.81 |
| seq | 16 | 128 | 2.86 |
| seq | 16 | 256 | 2.84 |
| seq | 16 | 1024 | 2.86 |
| seq | 16 | 16384 | 2.77 |
| seq | 64 | 64 | 72.64 |
| seq | 64 | 128 | 17.18 |
| seq | 64 | 256 | 11.33 |
| seq | 64 | 1024 | 11.40 |
| seq | 64 | 16384 | 9.68 |
| seq | 128 | 128 | 72.49 |
| seq | 128 | 256 | 24.73 |
| seq | 128 | 1024 | 15.78 |
| seq | 128 | 16384 | 14.75 |
| rand | 16 | 64 | 4.68 |
| rand | 16 | 128 | 2.82 |
| rand | 16 | 256 | 2.87 |
| rand | 16 | 1024 | 3.16 |
| rand | 16 | 16384 | 3.23 |
| rand | 64 | 64 | 7.02 |
| rand | 64 | 128 | 7.02 |
| rand | 64 | 256 | 7.11 |
| rand | 64 | 1024 | 8.00 |
| rand | 64 | 16384 | 8.12 |
| rand | 128 | 128 | 7.49 |
| rand | 128 | 256 | 7.59 |
| rand | 128 | 1024 | 8.47 |
| rand | 128 | 16384 | 8.70 |

### Single-thread mix at 1 GiB footprint: application GB/s and write-allocate-corrected DRAM traffic (model, not measured)

| Mix | application GB/s (IQR) | traffic factor (model) | modeled DRAM GB/s |
|---|---|---|---|
| 100% R | 72.5 (72.3 to 72.5) | 1.00 | 72.5 |
| 70/30 st | 100.3 (100.2 to 100.5) | 1.30 | 130.4 |
| 50/50 st | 113.4 (112.6 to 113.8) | 1.50 | 170.0 |
| 100% W st | 69.0 (68.9 to 69.1) | 2.00 | 138.0 |
| 70/30 stnp | 101.1 (101.1 to 101.5) | 1.00 | 101.1 |
| 50/50 stnp | 129.6 (128.8 to 129.6) | 1.00 | 129.6 |
| 100% W stnp | 143.9 (143.6 to 144.0) | 1.00 | 143.9 |
| 100% W dc zva | 273.2 (272.0 to 273.5) | 1.00 | 273.2 |
| 50/50 rmw | 135.1 (134.7 to 135.2) | 1.00 | 135.1 |

### Loaded latency by mix (probe thread + N bandwidth threads)

| Mix | N threads | app GB/s | probe ns | vs idle |
|---|---|---|---|---|
| 100% R | 4 | 262 | 140 | 1.22x |
| 100% R | 16 | 294 | 191 | 1.66x |
| 70/30 st | 4 | 260 | 162 | 1.41x |
| 70/30 st | 16 | 264 | 196 | 1.69x |
| 50/50 st | 4 | 240 | 178 | 1.54x |
| 50/50 st | 16 | 233 | 344 | 2.97x |
| 100% W st | 4 | 168 | 213 | 1.79x |
| 100% W st | 16 | 179 | 272 | 2.29x |
| 100% W stnp | 4 | 209 | 153 | 1.33x |
| 100% W stnp | 16 | 208 | 164 | 1.43x |
| 100% W dc zva | 4 | 313 | 170 | 1.44x |
| 100% W dc zva | 16 | 311 | 187 | 1.58x |
| 50/50 rmw | 4 | 342 | 193 | 1.63x |
| 50/50 rmw | 16 | 377 | 554 | 4.68x |

### Knee and Little's Law: lines in flight N = BW x latency / 128 B (idle latency 119 ns)

| Point | bandwidth | loaded latency | N (lines in flight) | config |
|---|---|---|---|---|
| highest BW with latency <= 1.5x idle | 302 GB/s | 150 ns | 353 | delay, 6 thr N=6, delay=0 |
| max BW / latency (power) point | 295 GB/s | 144 ns | 331 | threads N=5, delay=0 |
| maximum measured BW | 302 GB/s (66% of 460) | 150 ns | 353 | delay, 6 thr N=6, delay=0 |

### Single-core concurrency sweep: N_eff = throughput x L0 / 128 B with L0 = 109 ns (K = 1 latency)

| K chains | GB/s | ns per step | N_eff (lines) |
|---|---|---|---|
| 1 | 1.2 | 109 | 1.0 |
| 2 | 2.3 | 109 | 2.0 |
| 3 | 3.5 | 109 | 3.0 |
| 4 | 4.7 | 109 | 4.0 |
| 6 | 7.0 | 110 | 6.0 |
| 8 | 9.3 | 110 | 7.9 |
| 12 | 13.7 | 112 | 11.7 |
| 16 | 18.0 | 114 | 15.4 |
| 20 | 21.5 | 119 | 18.4 |
| 24 | 21.8 | 141 | 18.6 |
| 32 | 22.0 | 186 | 18.8 |
| 40 | 22.0 | 233 | 18.7 |
| 48 | 22.1 | 278 | 18.8 |
| 64 | 22.1 | 371 | 18.8 |

### All loaded-latency points (median over rounds)

| series | BW threads | delay iters | GB/s | latency ns | N lines |
|---|---|---|---|---|---|
| delay, 6 thr | 6 | 3200000 | 8.1 | 126 | 8 |
| delay, 6 thr | 6 | 1600000 | 15.9 | 125 | 16 |
| delay, 16 thr | 16 | 3200000 | 20.8 | 132 | 22 |
| delay, 6 thr | 6 | 800000 | 30.2 | 121 | 29 |
| delay, 16 thr | 16 | 1600000 | 41.0 | 136 | 44 |
| delay, 6 thr | 6 | 400000 | 55.9 | 123 | 54 |
| threads | 1 | 0 | 68.7 | 120 | 64 |
| delay, 16 thr | 16 | 800000 | 78.1 | 136 | 83 |
| delay, 6 thr | 6 | 200000 | 96.4 | 126 | 95 |
| threads | 2 | 0 | 136.2 | 129 | 137 |
| delay, 16 thr | 16 | 400000 | 140.5 | 147 | 161 |
| delay, 6 thr | 6 | 100000 | 154.6 | 131 | 159 |
| delay, 6 thr | 6 | 60000 | 199.8 | 137 | 213 |
| threads | 3 | 0 | 204.2 | 127 | 202 |
| delay, 16 thr | 16 | 200000 | 218.8 | 174 | 297 |
| threads | 4 | 0 | 262.4 | 138 | 283 |
| delay, 6 thr | 6 | 20000 | 270.5 | 139 | 294 |
| delay, 16 thr | 16 | 100000 | 284.2 | 174 | 386 |
| threads | 12 | 0 | 289.4 | 167 | 378 |
| delay, 16 thr | 16 | 0 | 294.2 | 192 | 441 |
| delay, 16 thr | 16 | 60000 | 294.5 | 183 | 422 |
| threads | 5 | 0 | 294.8 | 144 | 331 |
| threads | 14 | 0 | 295.1 | 186 | 430 |
| threads | 16 | 0 | 295.4 | 202 | 466 |
| delay, 16 thr | 16 | 20000 | 297.2 | 188 | 437 |
| threads | 10 | 0 | 298.7 | 154 | 360 |
| threads | 8 | 0 | 299.1 | 152 | 355 |
| threads | 6 | 0 | 300.4 | 150 | 353 |
| delay, 6 thr | 6 | 0 | 301.6 | 150 | 353 |

### Kernel cost: smallest vs largest footprint and AMAT-style prediction (hit time + miss ratio x (L(F) - L_L1) / N, N = 19 lines from Exp 4)

| Kernel | Pattern | ns/elem smallest | ns/elem largest | ratio | AMAT pred. largest ns | measured/pred. |
|---|---|---|---|---|---|---|
| mul | unit | 0.042 | 0.122 | 2.9x | 0.223 | 0.55 |
| mul | stride 64 B | 0.243 | 1.735 | 7.2x | 3.133 | 0.55 |
| mul | scattered | 0.232 | 10.556 | 45.5x | 6.014 | 1.76 |
| saxpy | unit | 0.044 | 0.079 | 1.8x | 0.224 | 0.35 |
| saxpy | stride 64 B | 0.245 | 1.232 | 5.0x | 3.124 | 0.39 |
| saxpy | scattered | 0.232 | 6.877 | 29.7x | 5.990 | 1.15 |

### TLB experiment: latency with one line per page vs the same number of lines packed (median ns)

| pages touched | paged | packed | difference |
|---|---|---|---|
| 8 | 0.12 | 0.12 | -0.00 |
| 16 | 0.66 | 0.66 | -0.00 |
| 32 | 0.66 | 0.66 | -0.00 |
| 64 | 0.66 | 0.66 | +0.00 |
| 128 | 0.66 | 0.66 | +0.00 |
| 256 | 1.97 | 0.66 | +1.31 |
| 512 | 1.97 | 0.66 | +1.32 |
| 1024 | 1.97 | 0.66 | +1.32 |
| 2048 | 5.90 | 2.58 | +3.32 |
| 4096 | 11.55 | 2.62 | +8.93 |
| 8192 | 12.50 | 2.76 | +9.74 |
| 16384 | 13.90 | 7.12 | +6.78 |
| 32768 | 16.56 | 7.61 | +8.95 |
| 65536 | 28.17 | 8.12 | +20.05 |

### Fixed 4 MiB of lines spread over P pages (median ns)

| P pages | ns |
|---|---|
| 256 | 7.64 |
| 512 | 8.12 |
| 1024 | 12.78 |
| 2048 | 26.97 |
| 4096 | 33.35 |
| 8192 | 40.36 |
| 16384 | 25.09 |
| 32768 | 19.18 |

### Pitfall 1: aggregate 'bandwidth' by total footprint (16 threads)

| total footprint | GB/s |
|---|---|
| 4 MiB | 1087 (1087 to 1088) |
| 16 MiB | 1094 (1094 to 1095) |
| 64 MiB | 357 (356 to 358) |
| 256 MiB | 298 (298 to 298) |
| 1 GiB | 296 (296 to 296) |
| 4 GiB | 275 (274 to 297) |

### Pitfall 4: clock estimate after 3 s idle vs steady (4.60 GHz)

| ms since burst start | GHz estimate | fraction of steady |
|---|---|---|
| 0 | 1.34 | 0.29 |
| 5 | 2.26 | 0.49 |
| 10 | 2.29 | 0.50 |
| 20 | 3.06 | 0.67 |
| 50 | 3.98 | 0.87 |
| 100 | 4.57 | 0.99 |
| 150 | 4.60 | 1.00 |
