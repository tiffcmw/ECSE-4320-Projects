Session 20261014-0029; frequency estimate 4.58 GHz.

### Placement check by cache signature (random chase ns; Super: L1D 128 KiB, L2 16 MiB; Performance: L1D 64 KiB, L2 8 MiB)

| QoS class | 48 KiB | 96 KiB | 6 MiB | 12 MiB |
|---|---|---|---|---|
| interactive | 0.66 | 0.66 | 8.14 | 11.53 |
| default | 0.66 | 0.66 | 7.96 | 10.28 |
| background | 2.25 | 13.35 | 42.08 | 137.70 |

### Zero-queue latency (random single-cycle chase, one thread, f = 4.58 GHz estimated)

| Level | Working set | ns, median (IQR) | cycles (est.) | n | Notes |
|---|---|---|---|---|---|
| L1 | 32 KiB | 0.66 (0.65 to 0.66) | 3 | 9 | within 128 KiB Super L1D; 64 KiB Performance L1D would miss here only above 64 KiB |
| L2 | 4 MiB | 7.64 (7.63 to 7.66) | 35 | 9 | within 8 MiB (Performance) and 16 MiB (Super) L2 |
| L2, near capacity | 12 MiB | 10.76 (9.53 to 10.97) | 49 | 9 | fits Super L2 (16 MiB) but not Performance L2 (8 MiB) |
| SLC region | 64 MiB | 93.76 (89.71 to 94.30) | 430 | 9 | beyond L2; SLC size unknown (not exposed), inside the ramp |
| DRAM | 1 GiB | 109.03 (109.00 to 109.51) | 500 | 9 | far beyond any cache; TLB misses included |
| DRAM (loaded harness, 0 BW threads) | 1 GiB | 111.2 | 509 |  | cross-check; separate process, probe thread only |

### Region edges inferred from the latency curve (first working set exceeding 1.5x the plateau; DRAM edge = within 10% of the largest-size value)

| Edge | Working set | sysctl capacity (Super) |
|---|---|---|
| L1 to L2 | 144 KiB | 128 KiB L1D |
| L2 to SLC | 13.4541 MiB | 16 MiB L2 |
| into DRAM plateau | 76.1084 MiB | SLC not exposed |

### Pointer-chase latency per node vs stride (DRAM footprint)

| Test | Order | Stride B | Latency | Implied line rate |
|---|---|---|---|---|
| chase | seq | 64 | 0.9 ns (0.9 to 0.9) | 138.1 GB/s line-rate |
| chase | seq | 128 | 7.8 ns (7.8 to 7.9) | 16.3 GB/s line-rate |
| chase | seq | 256 | 12.0 ns (12.0 to 12.0) | 10.7 GB/s line-rate |
| chase | seq | 512 | 13.6 ns (13.4 to 13.6) | 9.4 GB/s line-rate |
| chase | seq | 1024 | 6.9 ns (6.9 to 6.9) | 18.6 GB/s line-rate |
| chase | seq | 2048 | 103.7 ns (103.4 to 103.7) | 1.2 GB/s line-rate |
| chase | seq | 4096 | 110.3 ns (110.0 to 110.8) | 1.2 GB/s line-rate |
| chase | rand | 64 | 107.9 ns (107.9 to 108.1) | 1.2 GB/s line-rate |
| chase | rand | 128 | 108.8 ns (108.7 to 108.9) | 1.2 GB/s line-rate |
| chase | rand | 256 | 109.0 ns (108.6 to 109.1) | 1.2 GB/s line-rate |
| chase | rand | 512 | 108.4 ns (108.2 to 108.4) | 1.2 GB/s line-rate |
| chase | rand | 1024 | 108.4 ns (108.1 to 108.5) | 1.2 GB/s line-rate |
| chase | rand | 2048 | 109.1 ns (109.1 to 109.1) | 1.2 GB/s line-rate |
| chase | rand | 4096 | 114.9 ns (112.7 to 114.9) | 1.1 GB/s line-rate |

### Independent-load useful bandwidth (GB/s of bytes requested), selected points

| Order | Access B | Stride B | GB/s |
|---|---|---|---|
| seq | 16 | 64 | 27.65 |
| seq | 16 | 128 | 2.86 |
| seq | 16 | 256 | 2.84 |
| seq | 16 | 1024 | 2.86 |
| seq | 64 | 64 | 91.79 |
| seq | 64 | 128 | 15.67 |
| seq | 64 | 256 | 11.43 |
| seq | 64 | 1024 | 11.33 |
| seq | 128 | 128 | 91.10 |
| seq | 128 | 256 | 25.50 |
| seq | 128 | 1024 | 15.63 |
| rand | 16 | 64 | 4.66 |
| rand | 16 | 128 | 2.83 |
| rand | 16 | 256 | 2.87 |
| rand | 16 | 1024 | 3.20 |
| rand | 64 | 64 | 7.04 |
| rand | 64 | 128 | 7.02 |
| rand | 64 | 256 | 7.17 |
| rand | 64 | 1024 | 8.07 |
| rand | 128 | 128 | 7.55 |
| rand | 128 | 256 | 7.67 |
| rand | 128 | 1024 | 8.62 |

### Single-thread mix at 1 GiB footprint: application GB/s and write-allocate-corrected DRAM traffic (model, not measured)

| Mix | application GB/s (IQR) | traffic factor (model) | modeled DRAM GB/s |
|---|---|---|---|
| 100% R | 93.4 (91.3 to 94.3) | 1.00 | 93.4 |
| 70/30 st | 108.1 (107.6 to 108.2) | 1.30 | 140.6 |
| 50/50 st | 113.5 (113.1 to 114.2) | 1.50 | 170.3 |
| 100% W st | 68.7 (68.4 to 69.0) | 2.00 | 137.3 |
| 70/30 stnp | 116.8 (116.7 to 117.0) | 1.00 | 116.8 |
| 50/50 stnp | 129.8 (129.8 to 130.3) | 1.00 | 129.8 |
| 100% W stnp | 143.6 (143.6 to 143.7) | 1.00 | 143.6 |
| 100% W dc zva | 273.3 (270.4 to 274.2) | 1.00 | 273.3 |
| 50/50 rmw | 139.0 (138.6 to 139.5) | 1.00 | 139.0 |

### Loaded latency by mix (probe thread + N bandwidth threads)

| Mix | N threads | app GB/s | probe ns | vs idle |
|---|---|---|---|---|
| 100% R | 4 | 284 | 142 | 1.30x |
| 100% R | 16 | 292 | 449 | 4.10x |
| 70/30 st | 4 | 261 | 162 | 1.48x |
| 70/30 st | 16 | 261 | 367 | 3.35x |
| 50/50 st | 4 | 241 | 177 | 1.62x |
| 50/50 st | 16 | 236 | 209 | 1.90x |
| 100% W st | 4 | 168 | 212 | 1.93x |
| 100% W st | 16 | 181 | 418 | 3.80x |
| 100% W stnp | 4 | 209 | 153 | 1.40x |
| 100% W stnp | 16 | 213 | 164 | 1.50x |
| 100% W dc zva | 4 | 313 | 169 | 1.54x |
| 100% W dc zva | 16 | 322 | 185 | 1.69x |
| 50/50 rmw | 4 | 342 | 192 | 1.76x |
| 50/50 rmw | 16 | 380 | 244 | 2.23x |

### Knee and Little's Law: lines in flight N = BW x latency / 128 B (idle latency 111 ns)

| Point | bandwidth | loaded latency | N (lines in flight) | config |
|---|---|---|---|---|
| highest BW with latency <= 1.5x idle | 301 GB/s | 151 ns | 356 | threads N=6, delay=0 |
| max BW / latency (power) point | 297 GB/s | 146 ns | 338 | threads N=5, delay=0 |
| maximum measured BW | 301 GB/s (66% of 460) | 151 ns | 356 | threads N=6, delay=0 |

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
| 20 | 21.5 | 119 | 18.3 |
| 24 | 21.8 | 141 | 18.6 |
| 32 | 22.0 | 187 | 18.8 |
| 40 | 22.0 | 233 | 18.8 |
| 48 | 21.9 | 280 | 18.7 |
| 64 | 22.0 | 373 | 18.8 |

### All loaded-latency points (median over rounds)

| series | BW threads | delay iters | GB/s | latency ns | N lines |
|---|---|---|---|---|---|
| delay, 6 thr | 6 | 3200000 | 8.1 | 124 | 8 |
| delay, 6 thr | 6 | 1600000 | 16.0 | 119 | 15 |
| delay, 16 thr | 16 | 3200000 | 18.7 | 131 | 19 |
| delay, 6 thr | 6 | 800000 | 30.8 | 121 | 29 |
| delay, 16 thr | 16 | 1600000 | 39.7 | 134 | 42 |
| delay, 6 thr | 6 | 400000 | 57.0 | 124 | 55 |
| delay, 16 thr | 16 | 800000 | 65.1 | 142 | 72 |
| threads | 1 | 0 | 90.6 | 119 | 84 |
| delay, 6 thr | 6 | 200000 | 99.0 | 127 | 99 |
| delay, 16 thr | 16 | 400000 | 139.1 | 148 | 161 |
| delay, 6 thr | 6 | 100000 | 164.5 | 132 | 170 |
| threads | 2 | 0 | 166.3 | 126 | 163 |
| delay, 16 thr | 16 | 200000 | 214.8 | 174 | 292 |
| delay, 6 thr | 6 | 60000 | 215.7 | 130 | 220 |
| threads | 3 | 0 | 236.5 | 130 | 240 |
| threads | 10 | 0 | 262.1 | 154 | 315 |
| delay, 6 thr | 6 | 20000 | 278.5 | 140 | 305 |
| delay, 16 thr | 16 | 100000 | 281.1 | 177 | 389 |
| threads | 4 | 0 | 281.9 | 141 | 312 |
| delay, 16 thr | 16 | 60000 | 286.5 | 184 | 412 |
| threads | 12 | 0 | 288.6 | 175 | 395 |
| threads | 14 | 0 | 292.4 | 186 | 426 |
| delay, 16 thr | 16 | 0 | 293.8 | 189 | 435 |
| threads | 16 | 0 | 293.9 | 191 | 438 |
| delay, 16 thr | 16 | 20000 | 295.9 | 188 | 436 |
| threads | 5 | 0 | 297.0 | 146 | 338 |
| threads | 8 | 0 | 300.1 | 153 | 359 |
| delay, 6 thr | 6 | 0 | 300.8 | 151 | 355 |
| threads | 6 | 0 | 301.5 | 151 | 356 |

### Kernel cost: smallest vs largest footprint and AMAT-style prediction (hit time + miss ratio x (L(F) - L_L1) / N, N = 19 lines from Exp 4)

| Kernel | Pattern | ns/elem smallest | ns/elem largest | ratio | AMAT pred. largest ns | measured/pred. |
|---|---|---|---|---|---|---|
| mul | unit | 0.042 | 0.096 | 2.3x | 0.223 | 0.43 |
| mul | stride 64 B | 0.245 | 1.692 | 6.9x | 3.139 | 0.54 |
| mul | scattered | 0.232 | 10.576 | 45.7x | 6.020 | 1.76 |
| saxpy | unit | 0.045 | 0.079 | 1.8x | 0.225 | 0.35 |
| saxpy | stride 64 B | 0.247 | 1.221 | 4.9x | 3.133 | 0.39 |
| saxpy | scattered | 0.231 | 6.889 | 29.8x | 6.002 | 1.15 |

### TLB experiment: latency with one line per page vs the same number of lines packed (median ns)

| pages touched | paged | packed | difference |
|---|---|---|---|
| 8 | 0.12 | 0.12 | -0.00 |
| 16 | 0.66 | 0.66 | +0.00 |
| 32 | 0.66 | 0.65 | +0.00 |
| 64 | 0.66 | 0.66 | -0.00 |
| 128 | 0.66 | 0.65 | +0.00 |
| 256 | 1.97 | 0.66 | +1.31 |
| 512 | 1.97 | 0.66 | +1.31 |
| 1024 | 1.97 | 0.66 | +1.32 |
| 2048 | 7.41 | 2.58 | +4.83 |
| 4096 | 12.02 | 2.62 | +9.40 |
| 8192 | 12.49 | 2.75 | +9.74 |
| 16384 | 12.91 | 7.12 | +5.79 |
| 32768 | 18.77 | 7.63 | +11.14 |
| 65536 | 28.07 | 8.13 | +19.94 |

### Fixed 4 MiB of lines spread over P pages (median ns)

| P pages | ns |
|---|---|
| 256 | 7.63 |
| 512 | 8.09 |
| 1024 | 10.49 |
| 2048 | 21.26 |
| 4096 | 32.89 |
| 8192 | 39.98 |
| 16384 | 23.98 |
| 32768 | 14.44 |

### Pitfall 1: aggregate 'bandwidth' by total footprint (16 threads)

| total footprint | GB/s |
|---|---|
| 4 MiB | 1898 (1893 to 1909) |
| 16 MiB | 1866 (1859 to 1869) |
| 64 MiB | 360 (359 to 360) |
| 256 MiB | 297 (297 to 297) |
| 1 GiB | 295 (294 to 295) |
| 4 GiB | 296 (270 to 296) |

### Pitfall 4: clock estimate after 3 s idle vs steady (4.58 GHz)

| ms since burst start | GHz estimate | fraction of steady |
|---|---|---|
| 0 | 1.34 | 0.29 |
| 5 | 1.98 | 0.43 |
| 10 | 2.57 | 0.56 |
| 20 | 3.17 | 0.69 |
| 50 | 3.98 | 0.87 |
| 100 | 4.58 | 1.00 |
| 150 | 4.58 | 1.00 |
