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

## Amendment A (made after the smoke tests and before any experiment data was collected)

Smoke tests (3 s runs, `data/smoke/`, not used for any result) showed three things that change the design, not the predictions:

1. fio cannot run two 16-job processes at once on this Mac (`kern.sysv.shmall` is 4 MB for the whole system), so "several fio processes" is replaced by forked `posixaio` jobs (`thread=0`, `numjobs=k`, `iodepth=16`, configured QD = 16k). A 4 s probe gave effective depths of 31 (k=2) and 62 (k=4) by Little's Law, with 209 k and 231 k IOPS, against 187 k for `psync` at QD16. So the device was not yet saturated at QD16, and my "no more than 10% extra beyond QD16" prediction is at risk (the probe suggests about +20%). This is stated so the miss, if it happens, is not a surprise rewrite.
2. The knee rule is unchanged (smallest effective QD with at least 90% of peak IOPS) but is now evaluated over all Exp 4 points whose Little's-law check passes, across `psync` and forked `posixaio`. Engines differ in overhead, so the engine of each point is stated in the figure.
3. The sustained-write run measured about 12 GB/s in a 5 s probe (SMART host-bytes delta agreed with fio to 0.01%), twice my 3 to 6 GB/s guess, and a 300 s run would write about 3.7 TB. It is now capped at 2.2 TB (4 x 512 GiB) or 300 s, whichever comes first. Exp 2 write runs are shortened to 4 s (+1 s ramp) to keep write traffic near 1.5 TB. The 12 GB/s figure is an unplanned observation, so my Exp 2 / Exp 6 write-plateau predictions (2 to 5 GB/s, 4 to 6 GB/s burst) are probably too low; I leave them as written.

## Amendment B (also before any experiment data; supersedes parts of the engine facts and Amendment A item 1)

Between the first engine check and the smoke tests the Mac was upgraded from macOS 26.5.2 to 27.0.1 (found when the smoke data contradicted my engine-check conclusion). The OS limits changed: `kern.aiomax` 90 -> 1024 and `kern.aioprocmax` 16 -> 256. The 26.5.2 engine check is kept in `data/raw/engine_check_macos26.5.2/` and marked superseded; the engine check was repeated on 27.0.1 (`data/raw/engine_check_macos27.0.1/`). All experiment data, and the 32 GiB precondition, are taken on 27.0.1. fio's own limit of about 16 jobs (4 MB System V shared memory, `kern.sysv.shmall`, unchanged) still holds.

Consequences for the plan:

1. On 27.0.1 single-process `posixaio` reaches the configured depth (Little's Law: 15.8, 31.7, 63.7, 127.8, 255.2 for iodepth 16, 32, 64, 128, 256). So the "posixaio effective QD stays near 16" prediction in Exp 4 is withdrawn, and the forked-process design in Amendment A is dropped. Exp 4 is now: `psync` numjobs 1 to 16, plus `posixaio` iodepth 1 to 256 in one process. The Little's-law check still flags any point where effective and configured depth differ by more than 10%.
2. New Exp 4 prediction (made knowing the engine check on a 1 GiB file gave a plateau of 188 to 194 k IOPS from QD32 up, and 192 k for psync QD16): on the 32 GiB range, IOPS saturates between QD16 and QD64 at 180 to 250 k, past the plateau latency grows as QD / peak IOPS (QD256 about 1.0 to 1.4 ms mean), and the knee (90% of peak rule) falls at QD 8 to 32.
3. The Exp 7 "wrong effective queue depth" example becomes `psync` with `iodepth=64`: a synchronous engine ignores `iodepth`, so the real depth is 1. Prediction: IOPS and latency equal to the correct QD1 run (config A), about 14 k IOPS, and Little's Law reports an effective depth of 1.0 against a configured 64.
4. The 128 KiB sequential and write-plateau predictions in Exp 1, 2 and 6 are unchanged, with the caveat in Amendment A item 3 (writes appear faster than I guessed).
