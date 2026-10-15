Session 20261014-2046; frequency estimate 4.58 GHz.

### Placement check by cache signature (random chase ns; Super: L1D 128 KiB, L2 16 MiB; Performance: L1D 64 KiB, L2 8 MiB)

| QoS class | 48 KiB | 96 KiB | 6 MiB | 12 MiB |
|---|---|---|---|---|
| interactive | 0.66 | 0.66 | 7.96 | 10.92 |
| default | 0.65 | 0.66 | 7.93 | 11.15 |
| background | 2.19 | 16.41 | 36.23 | 108.66 |

### Zero-queue latency (random single-cycle chase, one thread, f = 4.58 GHz estimated)

| Level | Working set | ns, median (min to max) | cycles (est.) | n rounds | Notes |
|---|---|---|---|---|---|
| L1 | 32 KiB | 0.66 (0.65 to 0.72) | 3 | 12 | within 128 KiB Super L1D; 64 KiB Performance L1D would miss here only above 64 KiB |
| L2 | 4 MiB | 7.62 (7.58 to 8.05) | 35 | 12 | within 8 MiB (Performance) and 16 MiB (Super) L2 |
| L2, 2 MiB (128 pages) | 2 MiB | 7.12 (7.10 to 7.58) | 33 | 12 | smaller footprint than 4 MiB, so less translation cost |
| L2, near capacity | 12 MiB | 11.13 (8.94 to 13.27) | 51 | 12 | fits Super L2 (16 MiB) but not Performance L2 (8 MiB) |
| SLC region | 64 MiB | 91.89 (83.82 to 100.87) | 421 | 12 | beyond L2; SLC size unknown (not exposed), inside the ramp |
| DRAM | 1 GiB | 108.75 (108.42 to 122.01) | 498 | 12 | far beyond any cache; TLB misses included |
| DRAM (loaded harness, 0 BW threads) | 1 GiB | 112.7 | 516 |  | cross-check; separate process, probe thread only |

### Region edges inferred from the latency curve (first working set exceeding 1.5x the plateau; DRAM edge = within 10% of the largest-size value)

| Edge | Working set | sysctl capacity (Super) |
|---|---|---|
| L1 to L2 | 144 KiB | 128 KiB L1D |
| L2 to SLC | 13.4541 MiB | 16 MiB L2 |
| into DRAM plateau | 76.1084 MiB | SLC not exposed |

### Pointer-chase latency per node vs stride (DRAM footprint)

| Test | Order | Stride B | Latency | Implied line rate |
|---|---|---|---|---|
| chase | seq | 64 | 0.9 ns (0.9 to 1.3) | 136.4 GB/s line-rate |
| chase | seq | 128 | 7.8 ns (7.8 to 7.8) | 16.4 GB/s line-rate |
| chase | seq | 256 | 12.0 ns (11.9 to 12.1) | 10.7 GB/s line-rate |
| chase | seq | 512 | 14.3 ns (13.2 to 16.6) | 8.9 GB/s line-rate |
| chase | seq | 1024 | 6.8 ns (6.8 to 7.1) | 18.7 GB/s line-rate |
| chase | seq | 2048 | 103.4 ns (103.0 to 103.8) | 1.2 GB/s line-rate |
| chase | seq | 4096 | 110.6 ns (108.9 to 110.7) | 1.2 GB/s line-rate |
| chase | rand | 64 | 108.0 ns (107.5 to 108.1) | 1.2 GB/s line-rate |
| chase | rand | 128 | 108.4 ns (108.4 to 117.4) | 1.2 GB/s line-rate |
| chase | rand | 256 | 109.1 ns (108.4 to 110.0) | 1.2 GB/s line-rate |
| chase | rand | 512 | 108.3 ns (107.7 to 197.8) | 1.2 GB/s line-rate |
| chase | rand | 1024 | 108.2 ns (107.7 to 108.9) | 1.2 GB/s line-rate |
| chase | rand | 2048 | 109.3 ns (108.5 to 110.4) | 1.2 GB/s line-rate |
| chase | rand | 4096 | 113.6 ns (113.5 to 117.5) | 1.1 GB/s line-rate |

### Independent-load useful bandwidth (GB/s of bytes requested), selected points

| Order | Access B | Stride B | GB/s |
|---|---|---|---|
| seq | 16 | 64 | 27.96 |
| seq | 16 | 128 | 2.87 |
| seq | 16 | 256 | 2.84 |
| seq | 16 | 1024 | 2.87 |
| seq | 64 | 64 | 92.91 |
| seq | 64 | 128 | 15.76 |
| seq | 64 | 256 | 11.40 |
| seq | 64 | 1024 | 11.45 |
| seq | 128 | 128 | 93.24 |
| seq | 128 | 256 | 25.47 |
| seq | 128 | 1024 | 15.78 |
| rand | 16 | 64 | 4.68 |
| rand | 16 | 128 | 2.84 |
| rand | 16 | 256 | 2.89 |
| rand | 16 | 1024 | 3.27 |
| rand | 64 | 64 | 6.95 |
| rand | 64 | 128 | 7.00 |
| rand | 64 | 256 | 7.11 |
| rand | 64 | 1024 | 8.16 |
| rand | 128 | 128 | 7.53 |
| rand | 128 | 256 | 7.61 |
| rand | 128 | 1024 | 8.70 |

### Single-thread mix at 1 GiB footprint. Measured: application GB/s. Modeled (not measured): DRAM traffic if plain stores allocate

| Mix | measured application GB/s (min to max) | n rounds | modeled traffic factor | modeled DRAM GB/s |
|---|---|---|---|---|
| 100% R | 87.4 (81.8 to 91.7) | 9 | 1.00 (no allocate fetch assumed) |  |
| 70/30 st | 101.0 (87.6 to 104.0) | 9 | 1.30 | 131.3 |
| 50/50 st | 108.0 (99.2 to 109.4) | 9 | 1.50 | 162.1 |
| 100% W st | 68.2 (58.8 to 70.4) | 9 | 2.00 | 136.3 |
| 70/30 stnp | 105.4 (101.7 to 110.4) | 9 | 1.00 (no allocate fetch assumed) |  |
| 50/50 stnp | 122.2 (105.4 to 124.2) | 9 | 1.00 (no allocate fetch assumed) |  |
| 100% W stnp | 90.6 (81.6 to 91.7) | 9 | 1.00 (no allocate fetch assumed) |  |
| 50/50 rmw | 137.4 (128.5 to 139.4) | 9 | 1.00 (no allocate fetch assumed) |  |
| 100% W st (uniform) | 67.9 (46.2 to 74.0) | 9 | 2.00 | 135.9 |
| 100% W stnp (uniform) | 142.0 (118.4 to 144.1) | 9 | 1.00 (no allocate fetch assumed) |  |
| 100% W st (zero) | 277.3 (177.2 to 281.3) | 9 | 1.00 (no allocate fetch assumed) |  |
| 100% W stnp (zero) | 140.3 (109.7 to 143.6) | 9 | 1.00 (no allocate fetch assumed) |  |
| 100% W dc zva | 269.5 (257.4 to 275.8) | 9 | 1.00 (no allocate fetch assumed) |  |

### Loaded latency by mix (probe thread + N bandwidth threads)

| Mix | N threads | app GB/s | probe ns | vs idle | n rounds |
|---|---|---|---|---|---|
| 100% R | 4 | 273 | 142 | 1.26x | 6 |
| 100% R | 16 | 292 | 192 | 1.70x | 6 |
| 70/30 st | 4 | 246 | 165 | 1.48x | 6 |
| 70/30 st | 16 | 246 | 549 | 4.92x | 6 |
| 50/50 st | 4 | 226 | 178 | 1.59x | 6 |
| 50/50 st | 16 | 225 | 248 | 2.22x | 6 |
| 100% W st | 4 | 167 | 210 | 1.84x | 6 |
| 100% W st | 16 | 165 | 362 | 3.18x | 6 |
| 100% W stnp | 4 | 238 | 157 | 1.35x | 6 |
| 100% W stnp | 16 | 243 | 286 | 2.47x | 6 |
| 50/50 rmw | 4 | 337 | 193 | 1.71x | 6 |
| 50/50 rmw | 16 | 374 | 251 | 2.23x | 6 |

### Knee under two definitions fixed in advance (idle latency 113 ns; N = BW x latency / 128 B)

| Definition | point | bandwidth GB/s (min to max) | loaded latency ns (min to max) | latency vs idle | N lines in flight | n rounds |
|---|---|---|---|---|---|---|
| K1: fewest threads reaching 95% of maximum bandwidth | threads, 5 thr, delay 0 | 287 (190 to 298) | 149 (146 to 296) | 1.32x | 333 | 12 |
| K2: maximum bandwidth / latency | threads, 4 thr, delay 0 | 274 (236 to 288) | 142 (141 to 160) | 1.26x | 303 | 12 |
| maximum bandwidth | threads, 6 thr, delay 0 | 293 (211 to 302) | 153 (151 to 192) | 1.35x | 349 | 12 |

### Single-core concurrency sweep: N_eff = throughput x L0 / 128 B with L0 = 110 ns (K = 1 latency)

| K chains | GB/s (min to max) | ns per step | N_eff (lines) | n rounds |
|---|---|---|---|---|
| 1 | 1.2 (1.2 to 1.2) | 110 | 1.0 | 12 |
| 2 | 2.3 (2.3 to 2.4) | 110 | 2.0 | 12 |
| 3 | 3.5 (3.4 to 3.5) | 110 | 3.0 | 12 |
| 4 | 4.7 (4.6 to 4.7) | 110 | 4.0 | 12 |
| 6 | 6.9 (6.9 to 7.0) | 111 | 6.0 | 12 |
| 8 | 9.2 (9.1 to 9.3) | 111 | 7.9 | 12 |
| 12 | 13.6 (13.5 to 13.8) | 113 | 11.7 | 12 |
| 16 | 17.9 (17.8 to 18.1) | 114 | 15.4 | 12 |
| 20 | 21.3 (21.1 to 21.6) | 120 | 18.4 | 12 |
| 24 | 21.7 (21.0 to 21.9) | 142 | 18.7 | 12 |
| 32 | 21.8 (21.7 to 22.9) | 188 | 18.8 | 12 |
| 40 | 21.8 (21.6 to 22.1) | 235 | 18.8 | 12 |
| 48 | 21.8 (21.6 to 22.1) | 281 | 18.8 | 12 |
| 64 | 21.9 (21.5 to 22.1) | 374 | 18.9 | 12 |

### All loaded-latency points (median over rounds). N per thread is the Little's Law consistency check: it should stay near the one-core plateau while threads are not saturated

| series | BW threads | delay iters | GB/s | latency ns | N lines | N per thread | n rounds |
|---|---|---|---|---|---|---|---|
| delay, 6 thr | 6 | 3200000 | 8.1 | 125 | 8 | 1.3 | 12 |
| delay, 6 thr | 6 | 1600000 | 16.0 | 121 | 15 | 2.5 | 12 |
| delay, 16 thr | 16 | 3200000 | 20.1 | 138 | 22 | 1.4 | 12 |
| delay, 6 thr | 6 | 800000 | 30.8 | 123 | 30 | 4.9 | 12 |
| delay, 16 thr | 16 | 1600000 | 40.1 | 137 | 43 | 2.7 | 12 |
| delay, 6 thr | 6 | 400000 | 56.7 | 126 | 56 | 9.3 | 12 |
| delay, 16 thr | 16 | 800000 | 78.3 | 138 | 84 | 5.3 | 12 |
| threads | 1 | 0 | 87.7 | 121 | 83 | 83.0 | 12 |
| delay, 6 thr | 6 | 200000 | 97.5 | 129 | 99 | 16.4 | 12 |
| delay, 16 thr | 16 | 400000 | 139.9 | 151 | 165 | 10.3 | 12 |
| delay, 6 thr | 6 | 100000 | 162.0 | 133 | 168 | 28.0 | 12 |
| threads | 2 | 0 | 163.0 | 126 | 160 | 80.2 | 12 |
| delay, 6 thr | 6 | 60000 | 210.6 | 131 | 216 | 36.0 | 12 |
| delay, 16 thr | 16 | 200000 | 214.7 | 181 | 303 | 18.9 | 12 |
| threads | 3 | 0 | 228.7 | 132 | 235 | 78.4 | 12 |
| threads | 8 | 0 | 265.7 | 158 | 328 | 41.0 | 12 |
| delay, 6 thr | 6 | 20000 | 269.3 | 141 | 297 | 49.5 | 12 |
| threads | 4 | 0 | 273.6 | 142 | 303 | 75.8 | 12 |
| delay, 16 thr | 16 | 100000 | 276.4 | 183 | 394 | 24.6 | 12 |
| threads | 10 | 0 | 281.7 | 173 | 381 | 38.1 | 12 |
| delay, 16 thr | 16 | 60000 | 284.0 | 197 | 436 | 27.3 | 12 |
| threads | 12 | 0 | 285.0 | 201 | 446 | 37.2 | 12 |
| delay, 16 thr | 16 | 0 | 285.1 | 228 | 509 | 31.8 | 12 |
| delay, 16 thr | 16 | 20000 | 285.6 | 206 | 460 | 28.8 | 12 |
| threads | 5 | 0 | 286.6 | 149 | 333 | 66.6 | 12 |
| threads | 7 | 0 | 287.3 | 156 | 351 | 50.1 | 12 |
| threads | 14 | 0 | 287.4 | 230 | 516 | 36.8 | 12 |
| threads | 16 | 0 | 288.8 | 201 | 453 | 28.3 | 12 |
| delay, 6 thr | 6 | 0 | 292.7 | 152 | 347 | 57.9 | 12 |
| threads | 6 | 0 | 293.1 | 153 | 349 | 58.2 | 12 |

### Kernel cost: smallest vs largest footprint and AMAT-style prediction (hit time + miss ratio x (L(F) - L_L1) / N, N = 19 lines from Exp 4)

| Kernel | Pattern | ns/elem smallest | ns/elem largest | ratio | AMAT pred. largest ns | measured/pred. |
|---|---|---|---|---|---|---|
| mul | unit | 0.043 | 0.123 | 2.9x | 0.224 | 0.55 |
| mul | stride 64 B | 0.244 | 1.775 | 7.3x | 3.135 | 0.57 |
| mul | scattered | 0.232 | 10.766 | 46.5x | 6.013 | 1.79 |
| saxpy | unit | 0.045 | 0.079 | 1.8x | 0.224 | 0.35 |
| saxpy | stride 64 B | 0.247 | 1.238 | 5.0x | 3.110 | 0.40 |
| saxpy | scattered | 0.236 | 6.903 | 29.3x | 5.963 | 1.16 |

### Scattered vs unit-stride cost at the same footprint (the ratio depends strongly on the footprint)

| kernel | footprint | unit ns/elem | stride 64 B ns/elem | scattered ns/elem | scattered / unit | n rounds |
|---|---|---|---|---|---|---|
| mul | 12 KiB | 0.043 | 0.244 | 0.232 | 5.4x | 5 |
| mul | 6 MiB | 0.097 | 1.639 | 1.556 | 16.1x | 5 |
| mul | 1.5 GiB | 0.123 | 1.775 | 10.766 | 87.9x | 5 |
| saxpy | 8 KiB | 0.045 | 0.247 | 0.236 | 5.2x | 5 |
| saxpy | 4 MiB | 0.077 | 1.068 | 1.006 | 13.1x | 5 |
| saxpy | 1 GiB | 0.079 | 1.238 | 6.903 | 87.4x | 5 |

### Exp 7: median ns per load by layout. 'rand-packed' is the translation penalty after removing set conflicts; 'orig-packed' is the earlier definition

| pages (= lines) | original | random offsets | constant offset | packed | rand - packed | orig - packed | n rounds |
|---|---|---|---|---|---|---|---|
| 8 | 0.12 | 0.17 | 0.21 | 0.12 | +0.05 | -0.00 | 12 |
| 16 | 0.66 | 0.66 | 2.69 | 0.66 | +0.00 | +0.00 | 12 |
| 32 | 0.66 | 0.66 | 2.90 | 0.66 | -0.00 | -0.00 | 12 |
| 64 | 0.66 | 0.66 | 3.08 | 0.65 | +0.00 | +0.00 | 12 |
| 128 | 0.66 | 0.66 | 6.68 | 0.66 | +0.00 | +0.00 | 12 |
| 256 | 1.97 | 1.97 | 8.63 | 0.66 | +1.31 | +1.31 | 12 |
| 512 | 1.97 | 2.00 | 8.81 | 0.66 | +1.35 | +1.31 | 12 |
| 1024 | 1.97 | 2.93 | 26.31 | 0.66 | +2.28 | +1.32 | 12 |
| 2048 | 7.36 | 4.01 | 43.46 | 2.58 | +1.42 | +4.78 | 12 |
| 4096 | 11.99 | 8.02 | 46.93 | 2.62 | +5.39 | +9.37 | 12 |
| 8192 | 12.53 | 10.95 | 47.50 | 3.35 | +7.60 | +9.18 | 12 |
| 16384 | 12.94 | 13.09 | 69.27 | 7.13 | +5.96 | +5.81 | 12 |
| 32768 | 18.70 | 13.62 | 108.28 | 7.64 | +5.98 | +11.06 | 12 |
| 65536 | 24.39 | 15.35 | 108.92 | 8.11 | +7.24 | +16.29 | 12 |

### Fixed 4 MiB of lines spread over P pages (median ns)

| P pages | original | random offsets | constant offset |
|---|---|---|---|
| 256 | 7.64 | 7.62 | 7.63 |
| 512 | 8.10 | 8.12 | 8.12 |
| 1024 | 9.97 | 8.51 | 20.88 |
| 2048 | 22.08 | 8.75 | 41.54 |
| 4096 | 33.62 | 10.34 | 43.38 |
| 8192 | 40.01 | 11.87 | 61.05 |
| 16384 | 25.08 | 12.74 | 102.89 |
| 32768 | 18.51 | 13.60 | 108.12 |

### Pitfall 1: aggregate 'bandwidth' by total footprint (16 threads)

| total footprint | GB/s |
|---|---|
| 4 MiB | 1852 (1850 to 1856) |
| 16 MiB | 1814 (1726 to 1829) |
| 64 MiB | 354 (353 to 373) |
| 256 MiB | 294 (294 to 296) |
| 1 GiB | 288 (286 to 294) |
| 4 GiB | 293 (275 to 294) |

### Pitfall 4: clock estimate after 3 s idle vs steady (4.58 GHz)

| ms since burst start | GHz estimate | fraction of steady |
|---|---|---|
| 0 | 1.46 | 0.32 |
| 5 | 1.98 | 0.43 |
| 10 | 2.58 | 0.56 |
| 20 | 3.18 | 0.69 |
| 50 | 3.98 | 0.87 |
| 100 | 4.57 | 1.00 |
| 150 | 4.60 | 1.01 |

### Independent random 16 B loads: useful GB/s by stride, with and without hashed line offset in the block

| stride B | power of two | plain GB/s (min to max) | hashed offset GB/s | n rounds |
|---|---|---|---|---|
| 128 | yes | 2.80 (0.98 to 2.84) |  | 9 |
| 192 | no | 4.69 (2.10 to 4.72) |  | 9 |
| 256 | yes | 2.85 (1.94 to 2.88) | 2.84 | 9 |
| 320 | no | 4.58 (4.08 to 4.85) |  | 9 |
| 384 | no | 2.97 (2.80 to 3.00) |  | 9 |
| 512 | yes | 2.95 (2.35 to 2.97) | 3.04 | 9 |
| 640 | no | 3.12 (2.07 to 3.21) |  | 9 |
| 1024 | yes | 3.20 (2.74 to 3.25) | 3.51 | 9 |

### Kernels: ns per element by element stride at the two largest footprints, plain and hashed offset

| kernel | footprint | stride B | power of two | plain ns | hashed ns | n rounds |
|---|---|---|---|---|---|---|
| mul | 192 MiB | 4 | yes | 0.09 |  | 7 |
| mul | 192 MiB | 8 | yes | 0.25 |  | 7 |
| mul | 192 MiB | 16 | yes | 0.44 |  | 7 |
| mul | 192 MiB | 32 | yes | 0.89 |  | 7 |
| mul | 192 MiB | 64 | yes | 1.68 |  | 7 |
| mul | 192 MiB | 96 | no | 2.19 |  | 7 |
| mul | 192 MiB | 128 | yes | 15.45 |  | 7 |
| mul | 192 MiB | 192 | no | 4.25 |  | 7 |
| mul | 192 MiB | 256 | yes | 14.30 | 16.23 | 7 |
| mul | 192 MiB | 320 | no | 6.56 |  | 7 |
| mul | 192 MiB | 384 | no | 16.89 |  | 7 |
| mul | 192 MiB | 512 | yes | 11.46 | 13.78 | 7 |
| mul | 192 MiB | 640 | no | 16.83 |  | 7 |
| mul | 192 MiB | 1024 | yes | 8.95 | 15.44 | 7 |
| mul | 768 MiB | 4 | yes | 0.10 |  | 7 |
| mul | 768 MiB | 8 | yes | 0.25 |  | 7 |
| mul | 768 MiB | 16 | yes | 0.44 |  | 7 |
| mul | 768 MiB | 32 | yes | 0.89 |  | 7 |
| mul | 768 MiB | 64 | yes | 1.68 |  | 7 |
| mul | 768 MiB | 96 | no | 2.19 |  | 7 |
| mul | 768 MiB | 128 | yes | 15.91 |  | 7 |
| mul | 768 MiB | 192 | no | 4.42 |  | 7 |
| mul | 768 MiB | 256 | yes | 16.05 | 17.57 | 7 |
| mul | 768 MiB | 320 | no | 6.47 |  | 7 |
| mul | 768 MiB | 384 | no | 17.16 |  | 7 |
| mul | 768 MiB | 512 | yes | 15.90 | 17.20 | 7 |
| mul | 768 MiB | 640 | no | 17.04 |  | 7 |
| mul | 768 MiB | 1024 | yes | 16.03 | 16.85 | 7 |
| saxpy | 128 MiB | 4 | yes | 0.08 |  | 7 |
| saxpy | 128 MiB | 8 | yes | 0.24 |  | 7 |
| saxpy | 128 MiB | 16 | yes | 0.31 |  | 7 |
| saxpy | 128 MiB | 32 | yes | 0.58 |  | 7 |
| saxpy | 128 MiB | 64 | yes | 1.20 |  | 7 |
| saxpy | 128 MiB | 96 | no | 1.39 |  | 7 |
| saxpy | 128 MiB | 128 | yes | 10.98 |  | 7 |
| saxpy | 128 MiB | 192 | no | 3.41 |  | 7 |
| saxpy | 128 MiB | 256 | yes | 9.31 | 10.42 | 7 |
| saxpy | 128 MiB | 320 | no | 4.56 |  | 7 |
| saxpy | 128 MiB | 384 | no | 10.87 |  | 7 |
| saxpy | 128 MiB | 512 | yes | 5.95 | 8.33 | 7 |
| saxpy | 128 MiB | 640 | no | 10.81 |  | 7 |
| saxpy | 128 MiB | 1024 | yes | 5.16 | 9.77 | 7 |
| saxpy | 512 MiB | 4 | yes | 0.08 |  | 7 |
| saxpy | 512 MiB | 8 | yes | 0.24 |  | 7 |
| saxpy | 512 MiB | 16 | yes | 0.31 |  | 7 |
| saxpy | 512 MiB | 32 | yes | 0.58 |  | 7 |
| saxpy | 512 MiB | 64 | yes | 1.21 |  | 7 |
| saxpy | 512 MiB | 96 | no | 1.43 |  | 7 |
| saxpy | 512 MiB | 128 | yes | 11.49 |  | 7 |
| saxpy | 512 MiB | 192 | no | 3.70 |  | 7 |
| saxpy | 512 MiB | 256 | yes | 11.54 | 12.19 | 7 |
| saxpy | 512 MiB | 320 | no | 4.94 |  | 7 |
| saxpy | 512 MiB | 384 | no | 11.53 |  | 7 |
| saxpy | 512 MiB | 512 | yes | 11.29 | 11.51 | 7 |
| saxpy | 512 MiB | 640 | no | 11.56 |  | 7 |
| saxpy | 512 MiB | 1024 | yes | 9.84 | 11.26 | 7 |

### Read ceiling tests: aggregate read GB/s by thread count

| variant | 1 thr | 2 thr | 4 thr | 6 thr | 8 thr | 12 thr | 16 thr |
|---|---|---|---|---|---|---|---|
| standard ld1 x4 (e4) | 88 | 163 | 274 | 293 | 266 | 285 | 289 |
| ldp q-pairs | 94 | 168 | 279 | 292 | 301 | 293 | 293 |
| ld1 four-register | 94 | 170 | 288 | 301 | 301 | 293 | 292 |
| background QoS only | 33 | 43 | 42 | 43 | 45 | 45 | 46 |
| random buffer content |  |  | 284 | 285 |  |  | 292 |

### Read plus concurrent writer threads (stnp or st, random data); writer GB/s is application bytes

| writers | read threads | read GB/s (min to max) | writer GB/s | total GB/s | n rounds |
|---|---|---|---|---|---|
| none | 4 | 274 (236 to 288) | 0 | 274 | 12 |
| none | 6 | 293 (211 to 302) | 0 | 293 | 12 |
| 2 stnp writers | 4 | 182 (168 to 193) | 154 | 336 | 7 |
| 2 stnp writers | 6 | 205 (189 to 228) | 150 | 355 | 7 |
| 2 st writers | 4 | 176 (165 to 183) | 85 | 261 | 7 |
| 2 st writers | 6 | 218 (196 to 227) | 65 | 282 | 7 |

### Plateau tests: median ns per load by footprint

| footprint | 64 B spacing | 128 B spacing | 256 B spacing | mutating walk |
|---|---|---|---|---|
| 48 KiB | 0.67 | 0.67 | 0.66 | 2.40 |
| 57 KiB | 0.67 | 0.66 | 0.66 | 2.41 |
| 67 KiB | 0.66 | 0.66 | 0.66 | 2.39 |
| 80 KiB | 0.67 | 0.66 | 0.67 | 2.41 |
| 96 KiB | 0.67 | 0.69 | 0.66 | 2.40 |
| 114 KiB | 0.67 | 0.68 | 0.67 | 2.40 |
| 135 KiB | 1.11 | 1.12 | 1.49 | 2.48 |
| 161 KiB | 1.96 | 2.15 | 2.53 | 2.79 |
| 192 KiB | 2.19 | 2.45 | 2.62 | 3.03 |
| 228 KiB | 2.78 | 2.58 | 2.63 | 3.25 |
| 271 KiB | 2.88 | 2.62 | 2.62 | 3.45 |
| 322 KiB | 2.85 | 2.62 | 2.64 | 3.62 |
| 384 KiB | 2.86 | 2.68 | 2.64 | 3.75 |
| 456 KiB | 2.87 | 2.65 | 2.63 | 3.92 |
| 543 KiB | 2.88 | 2.65 | 2.65 | 3.99 |
| 645 KiB | 2.87 | 2.66 | 2.64 | 4.09 |
| 768 KiB | 2.91 | 2.66 | 2.64 | 4.18 |
| 913 KiB | 2.90 | 2.71 | 2.67 | 4.34 |
| 1.06055 MiB | 5.18 | 5.14 | 5.01 | 4.63 |
| 1.26074 MiB | 7.19 | 7.31 | 7.16 | 5.31 |
| 1.5 MiB | 7.23 | 7.23 | 7.21 | 5.90 |
| 1.7832 MiB | 7.18 | 7.35 | 7.25 | 6.38 |
| 2.12109 MiB | 7.17 | 7.18 | 7.32 | 6.87 |
| 2.52246 MiB | 7.16 | 7.29 | 7.26 | 7.22 |
| 3 MiB | 7.40 | 7.48 | 7.40 | 7.84 |
| 3.56738 MiB | 7.61 | 7.64 | 7.59 | 8.14 |
| 4.24219 MiB | 7.75 | 7.71 | 7.73 | 8.55 |
| 5.04492 MiB | 7.84 | 7.93 | 7.92 | 8.81 |
| 6 MiB | 7.96 | 8.03 | 8.03 | 9.12 |
