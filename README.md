# ECSE 4320/6320 Class-wide Projects 1, 2 and 3

Course: ECSE 4320/6320 (Advanced Computer Systems), class-wide projects, October 2026.

Team: Tiffany Cheng (Student A, Member A), Marie Morales (Student B, Member B) and Alex Redd (Student C, Member C). The Project 2 and Project 3 reports name them in Appendix A; the Project 1 report says only "three students" there. The split of work is in Appendix A of each report.

| Project | What was measured | Headline results (from the report) | Folder | Report |
|---|---|---|---|---|
| 1. SIMD advantage profiling | Single-thread NEON vectorization of SAXPY, multiply, dot product and a 3-point stencil (f32, f64, u32), 4 KiB to 2 GiB, plus alignment, tails, stride, gather, roofline and a flawed benchmark | f32 SAXPY is 5.2x faster than the default scalar build, 2.1x faster than an unrolled loop and 1.35x in DRAM. SAXPY bandwidth stays at 147 to 154 GiB/s from 256 KiB to 1 GiB. The fast-math dot product is 14.0x faster than the strict loop, of which 8.4x is independent accumulators and 1.7x SIMD | [Project-1/](Project-1/) | [Project-1/report/Project1_Report.pdf](Project-1/report/Project1_Report.pdf) |
| 2. Cache and memory profiling | Latency, bandwidth, concurrency, cache and TLB behavior with own C benchmarks (no Intel MLC on macOS) | L1 0.66 ns, DRAM 108.7 ns. One core sustains about 19 outstanding misses (21.9 GB/s). Chip read bandwidth saturates at 293 GB/s (64% of the 460 GB/s peak); read-modify-write reaches 374 GB/s (81%) | [Project-2/](Project-2/) | [Project-2/report/Project2_Report.pdf](Project-2/report/Project2_Report.pdf) |
| 3. SSD profiling | Internal SSD (APPLE SSD AP2048Z) through one 32 GiB file on APFS with direct I/O, using fio | 4 KiB random read at QD1 takes 55 to 70 µs; reads reach 12.9 GB/s, writes about 10.6 GB/s. 4 KiB random reads saturate at 189 k to 223 k IOPS with the knee at QD16. A 2.2 TB sustained write held 11.0 GB/s with no cliff | [Project-3/](Project-3/) | [Project-3/report/Project3_Report.pdf](Project-3/report/Project3_Report.pdf) |

Machine (all three projects): Apple M5 Max MacBook Pro, 18 cores (6 Super + 12 Performance), 36 GB unified memory. Projects 1 and 2 ran on macOS 26.5.2 (build 25F84); the OS was upgraded to macOS 27.0.1 during Project 3, and all Project 3 experiments ran on 27.0.1.

## How to review

1. Read the report PDF of a project first. Each report is self-contained: method, results, hypotheses scored against results, limitations.
2. Open the project README to reproduce it. Each README maps every report table and figure to the script and data file that produce it, and gives a quick mode (Projects 1 and 2: about 2 and 4 minutes) or a re-analysis from the stored raw data (Project 3).

`Project-A1/` is a separate Track A project (Advanced OS and CPU Feature Exploration) and is not covered by these three reports.

## AI use

See Appendix A (AI-use note) of each report: [Project 1](Project-1/report/Project1_Report.pdf), [Project 2](Project-2/report/Project2_Report.pdf), [Project 3](Project-3/report/Project3_Report.pdf). Repository notes are in `Project-1/docs/AI_USE.md`, `Project-2/docs/AI_USE.md` and `Project-3/AI_USE.md`.
