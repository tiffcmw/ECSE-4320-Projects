# Pre-experiment hypotheses (written and committed before any experiment data was collected)

Platform: Apple M5 Max MacBook Pro, APPLE SSD AP2048Z (2 TB, controller inside the SoC), APFS on a FileVault volume, macOS 26.5.2, fio 3.43. Test file: one 32 GiB file, direct I/O (F_NOCACHE), incompressible data.

## What I had already seen before writing this (disclosure)

The only measurements taken before this file are the 5-second engine checks on a separate 1 GiB file (`data/raw/engine_check/`). They were plumbing tests to see whether queue depth is real, not experiments. They showed: 4 KiB random read at QD1 about 70 to 76 microseconds (13 to 14 k IOPS); `psync` with `numjobs=16` about 187 k IOPS; `posixaio` never exceeds an effective depth of about 16 even when `iodepth=32` or `64` (macOS `kern.aioprocmax=16`). So my QD1 read-latency and QD-knee guesses below are informed by that; the other hypotheses are not.

Engine facts that shape every experiment (measured, not hypothesised): no libaio or io_uring on macOS; fio supports at most 16 jobs in one process (4 MB System V shared-memory limit), so effective queue depth above 16 needs several fio processes at once.

Queue depth in all experiments is produced with `psync` and `numjobs=N` (effective QD = N, verified with Little's Law). `posixaio` is used only as a cross-check.

Conventions: "QD16" means 16 psync jobs. All numbers are predictions with a rough range; a result outside the range counts as a miss and will be reported as one.

## Exp 1. Zero-queue baselines (QD1, 1 job)

| Workload | Predicted mean latency | Predicted throughput | Reason |
|---|---|---|---|
| 4 KiB random read | 60 to 90 us | 11 to 16 k IOPS (45 to 65 MB/s) | One flash page read (tens of us) plus controller, encryption, APFS and syscall overhead. At QD1 nothing hides this latency. |
| 4 KiB random write | 20 to 60 us, lower than read | 15 to 50 k IOPS | The controller acknowledges from a write buffer before NAND programming (programming takes hundreds of us, so a program-time latency would be a surprise). APFS copy-on-write adds some cost. |
| 128 KiB sequential read | 70 to 150 us | 0.9 to 1.8 GB/s | Read of 32 pages striped across channels, so one request already uses parallelism, but with one request in flight the device idles between requests. |
| 128 KiB sequential write | 80 to 200 us | 0.7 to 1.6 GB/s | Same, absorbed by the write buffer / SLC cache. |

Tail: p99 about 1.5 to 3 times p50; p95 close to p50. Writes will have a heavier tail than reads (buffer flushes, APFS metadata).

## Exp 2. Block-size sweep (QD16, 4 to 256 KiB, sequential also to 1 MiB)

- Throughput (MB/s) rises with block size and saturates: random read from about 0.7 GB/s at 4 KiB to a plateau of 5 to 7 GB/s at 128 to 256 KiB; sequential read reaches the plateau by 64 to 128 KiB.
- IOPS falls with block size after the small sizes (per-IO overhead dominates at 4 to 16 KiB, bandwidth dominates above 64 KiB).
- Latency is flat from 4 to about 16 KiB (one or two flash pages), then grows roughly linearly with size once the interface/channel bandwidth is the limit (queueing at QD16: latency is about 16 x size / bandwidth).
- Random approaches sequential at 128 KiB and above, because the controller already stripes large requests; the random-vs-sequential gap is largest at 4 to 16 KiB.
- Writes follow the same shape, saturating at a lower plateau than reads (2 to 5 GB/s) because programming is slower than reading.

## Exp 3. Read/write mix (4 KiB random, QD16)

- 100% read gives the highest read IOPS; pure write IOPS is in the same order of magnitude (write buffer helps) and may be higher or lower than read (uncertain).
- Mixed workloads (70/30, 50/50) will show total IOPS below a linear blend of the two pure cases (a "mixing penalty"), because reads wait behind NAND programs and garbage collection on the same dies.
- Read latency rises with write share: 50/50 read mean latency 1.3 to 3 times the 100% read value. Write latency in mixes stays below read latency while the buffer absorbs it.

## Exp 4. Queue-depth sweep (4 KiB random read)

- IOPS rises almost linearly with QD at first (QD1 to QD4, latency about flat at about 70 us), then bends and saturates at about 180 to 300 k IOPS.
- Knee (defined in advance as the smallest QD reaching 90% of peak IOPS): QD 8 to 16.
- Past the knee, IOPS is flat and latency grows in proportion to QD. This is Little's Law with throughput pinned: outstanding = IOPS x latency, so latency = QD / peak IOPS.
- Little's Law check should agree with configured QD within 5% for psync with `numjobs=N`. For `posixaio` I expect the effective depth to stay near 16 whatever `iodepth` is set to (seen in the engine check), and the check will flag those points.
- Beyond QD16 (several fio processes) the device is already saturated, so I expect no more than 10% extra IOPS.

## Exp 5. Tail latency (4 KiB random read, 60 s, 3 trials)

- Mid-QD (QD4): p50 about 70 us, p99 about 1.5 to 2.5 times p50, p99.9 about 3 to 8 times p50.
- Near-knee QD (from Exp 4): p50 is higher by queueing; p99.9 relative to p50 is wider than at mid-QD because the tail now includes waiting behind other requests plus occasional controller / OS scheduling stalls.
- Percentile spread (p99.9/p50) will be larger at the knee than at mid-QD. If it is not, the tail is dominated by device-internal events rather than queueing, which would be a surprise.
- Sample count: at least 3 million IOs per run, so p99.9 has about 3000 samples and p99.99 about 300.

## Exp 6. Working-set and device state

- Range: 4 KiB random read on a 1 GiB range vs the full 32 GiB: within 10% of each other (flash read cost does not depend on LBA range). A small range may be slightly faster if the controller's mapping cache covers it. For random writes, the small 1 GiB range may be a little faster (less spread-out mapping, easier garbage collection), also within about 20%.
- Sustained write (sequential 1 MiB writes, 4 jobs, 5 minutes): burst at 4 to 6 GB/s at first. The drive may fall to a lower steady rate (30 to 60% lower) after the SLC-style cache fills. I give it about 50% that a clear drop appears in 5 minutes (with 1.2 TB free, the dynamic cache is large; Apple tunes the drive to keep throughput up). If there is no cliff I will report "no cliff observed" and list what I checked. Thermal throttling in a laptop is a second possible cause of a decline and I cannot separate the two with the data available (no SSD temperature log beyond SMART snapshots).
- Expected write volume of this run: about 0.9 to 1.8 TB (5 minutes at 3 to 6 GB/s). Actual bytes written are logged from fio and from the SMART counter.

## Exp 7. Misleading setup (page cache)

- 4 KiB random read, QD1, on a 1 GiB range that fits in RAM: buffered (`direct=0`) reads show 1 to 5 us mean latency and 50 to 300 times the IOPS of direct reads (70 us), once the pages are warm. This is a measurement of the page cache and memory, not the SSD.
- Proof by difference: same job, same file, only `direct` changes. If the buffered number is not far above the direct number, then `direct=1` is not doing what I think (this is also the pre-run direct-I/O check).
- Second misleading setup: `posixaio` with `iodepth=64`. Predicted effective QD is about 16, not 64, so throughput is no higher than at `iodepth=16`.
