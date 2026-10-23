// Builds Project3_SSD_Report.docx. Every table comes from report/docx_data.json (written by scripts/export_docx_data.py
// from data/processed); figures from plots/docx/. Prose numbers are checked by scripts/check_docx_numbers.py.
const fs = require("fs"); const path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Footer, AlignmentType, HeadingLevel, BorderStyle,
        WidthType, ShadingType, PageNumber, LevelFormat, TabStopType } = D;
const ROOT = path.resolve(__dirname, "../.."); const DATA = JSON.parse(fs.readFileSync(ROOT + "/report/docx_data.json"));
const W = 9936;                                   // content width in DXA (Letter, 0.8 inch margins)
const FONT = "Calibri", MONO = "Courier New";

function runs(text, base = {}) {                  // **bold**, *italic*, `code`, [STUDENT TO FILL: ...] highlighted
  const out = []; const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[STUDENT TO FILL[^\]]*\])/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: MONO, size: (base.size || 20) - 2, ...base, font: MONO }));
    else if (t.startsWith("[")) out.push(new TextRun({ text: t, bold: true, highlight: "yellow", ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (text, o = {}) => new Paragraph({ children: runs(text, o.run || {}), spacing: { after: o.after ?? 90, line: 252 }, alignment: o.align, keepNext: o.keepNext, indent: o.indent });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t })], keepNext: true });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t })], keepNext: true });
const B = (text) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(text), spacing: { after: 50, line: 252 } });
const CAP = (text) => new Paragraph({ children: runs(text, { size: 17, italics: false, color: "333333" }), spacing: { before: 40, after: 140 }, keepLines: true });
const TCAP = (text) => new Paragraph({ children: runs(text, { size: 17, color: "333333" }), spacing: { before: 100, after: 50 }, keepNext: true });

const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" }; const borders = { top: border, bottom: border, left: border, right: border };
function table(rows, weights, o = {}) {
  const tot = weights.reduce((a, b) => a + b, 0); const cw = weights.map((w) => Math.round((w / tot) * W)); cw[cw.length - 1] += W - cw.reduce((a, b) => a + b, 0);
  const sz = o.size || 16;
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cw,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.map((c, j) => new TableCell({
      width: { size: cw[j], type: WidthType.DXA }, borders, margins: { top: 30, bottom: 30, left: 70, right: 70 },
      shading: i === 0 ? { fill: "DCE6F2", type: ShadingType.CLEAR, color: "auto" } : (o.firstColBold && j === 0 ? { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" } : undefined),
      children: [new Paragraph({ children: runs(String(c), { size: sz, bold: i === 0 }), spacing: { after: 0, line: 228 }, keepNext: rows.length <= 12 && i < rows.length - 1, alignment: (o.numeric && j > 0 && i > 0) ? AlignmentType.RIGHT : AlignmentType.LEFT })] })) })) });
}
function fig(name, widthIn, cap) {
  const [pw, ph] = DATA.fig[name]; const w = Math.round(widthIn * 96), h = Math.round(w * ph / pw);
  return [new Paragraph({ children: [new ImageRun({ type: "png", data: fs.readFileSync(`${ROOT}/plots/docx/${name}`), transformation: { width: w, height: h },
    altText: { title: name, description: cap, name } })], alignment: AlignmentType.CENTER, spacing: { before: 60, after: 0 }, keepNext: true }), CAP(cap)];
}
const sp = () => new Paragraph({ children: [], spacing: { after: 60 } });
let T = 0, F = 0; const tcap = (t) => TCAP(`**Table ${++T}.** ${t}`); const fcap = (t) => `**Figure ${++F}.** ${t}`;
const LAB = (l, t) => P(`**${l}** ${t}`);
const C = [];                                      // document body

// ---------- title block
C.push(new Paragraph({ children: [new TextRun({ text: "ECSE 4320/6320 Class-wide Project 3", size: 22, color: "555555" })], spacing: { after: 40 } }));
C.push(new Paragraph({ children: [new TextRun({ text: "SSD Performance Profiling", bold: true, size: 40, color: "1F3864" })], spacing: { after: 20 } }));
C.push(new Paragraph({ children: [new TextRun({ text: "Apple M5 Max internal NVMe SSD, APFS, macOS 27.0.1, fio 3.43", size: 24, color: "1F3864" })], spacing: { after: 100 } }));
C.push(P("Team: [STUDENT TO FILL: Student A name], [STUDENT TO FILL: Student B name], [STUDENT TO FILL: Student C name]", { after: 30 }));
C.push(new Paragraph({ children: runs("Submitted: [STUDENT TO FILL: date]    Repository: ECSE-4320-Projects, folder Project-3", { size: 18, color: "555555" }), border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "1F3864", space: 4 } }, spacing: { after: 140 } }));

// ---------- summary
C.push(H1("Summary"));
C.push(P("This report profiles the internal SSD of an M5 Max MacBook Pro (APPLE SSD AP2048Z, 2 TB, controller inside the SoC) through one 32 GiB file on APFS with direct I/O. **Measured:** 4 KiB random read at queue depth 1 takes 55 to 70 µs; reads reach 12.9 GB/s and writes about 10.6 GB/s; 4 KiB random reads saturate at 189 k to 223 k IOPS with the knee at QD16, while 4 KiB random writes reach only 47 k IOPS. A 2.2 TB sustained sequential write held 11.0 GB/s with no cliff, a result limited by the test and not proof that no SLC-style cache exists. A page-cache run inflates IOPS 90 times (1.32 M against 14.5 k). The same read workload ran at two speed levels (about 189 k and 222 k IOPS) for a reason that could not be established. Predictions written before data collection are scored in Section 9, including the misses. Claims are labeled **measured**, **inferred** or **hypothesis**."));

// ---------- 1 methodology
C.push(H1("1. Methodology"));
C.push(table([["Item", "Value"],
  ["Platform", "MacBook Pro, Apple M5 Max (6 performance + 12 efficiency cores), 36 GiB RAM, macOS 27.0.1. The OS was upgraded from 26.5.2 mid-project; precondition and all experiments ran on 27.0.1."],
  ["SSD", "APPLE SSD AP2048Z, 2 TB, NVMe-class, controller integrated in the SoC, TRIM supported, wear 0%. PCIe link generation and width cannot be read on macOS."],
  ["Filesystem", "A file on APFS (4 KiB blocks), not a raw device. FileVault is on, so hardware encryption and copy-on-write are part of every number. Logical file offsets are not device LBAs."],
  ["fio and engines", "fio 3.43. Available: `psync` (and other synchronous engines), `posixaio`, `mmap`. **Not available on macOS:** `libaio`, `io_uring` (detected at run time, recorded in `data/raw/engine_check_macos27.0.1/`). Fallback: `psync` with `numjobs=N`, and `posixaio` with `iodepth=N`."],
  ["Queue depth", "`psync` depth = `numjobs` (fio supports only about 16 jobs here: macOS limits System V shared memory to 4 MB). `posixaio` reaches depth 256 in one process on macOS 27.0.1 (`kern.aioprocmax` was 16 on 26.5.2). Effective depth is checked for every run with IOPS x mean latency."],
  ["Test file and range", "One 32 GiB file in a Spotlight-excluded directory. Offsets span 0 to 32 GiB (1 GiB for the range test), always block-aligned."],
  ["Data pattern", "`refill_buffers=1`, `buffer_compress_percentage=0`: incompressible, fresh random data per IO, identical for every job."],
  ["Preconditioning", "File written once sequentially (4 jobs, 1 MiB blocks, 32.0 GiB at 6.2 GB/s) before any read test, so reads hit allocated blocks."],
  ["Power, thermal, load", "AC power, Low Power Mode off, battery held at 80% by macOS. SMART temperature, wear, free space, `pmset` state and top CPU consumers logged before and after every stage. Desktop apps were running at a few percent CPU, so the machine was not perfectly idle."],
  ["Repetitions and timing", "3 trials per point (mean and sample sd), except Exp 6b (one run, capped by the project owner). Runtime / ramp: Exp 1 30 s / 5 s; Exp 2 reads 15 s / 2 s, writes 4 s / 1 s (shortened to limit wear); Exp 3, 4, 6a 20 s / 3 s; Exp 5 60 s / 5 s; Exp 7 20 s / 5 s."],
  ["Validity guards", "Before every run: AC power required. After every run: result moved to `data/raw/invalid/` and the stage aborted if the Mac left AC power or the run took longer than runtime + ramp + 45 s. Each stage runs under `caffeinate`. Free space after the file must stay above 20%; every fio target must resolve inside the scratch directory."]],
  [2.2, 9], { firstColBold: true }));
C.push(sp());
C.push(P("**Direct I/O verification.** `F_NOCACHE` itself was not traced (that needs sudo and relaxed SIP), so the evidence is behavioral: (1) on the same file and 1 GiB range, QD1 4 KiB random read gave 61.4 µs with `direct=1` and 0.70 µs with `direct=0` (87 times lower), and the check script stops the whole campaign if `direct=1` looks cache-like; (2) the SSD's own SMART \"Data Units Read\" counter never fell below fio's byte count (ratio 1.11 to 1.55, the excess being ramp-time IO that fio does not count; the 1.55 for Exp 3 and 4 includes writes and is unexplained beyond ramp time); (3) fio's written bytes equal the SMART \"Data Units Written\" delta to 0.01% (2.199 TB each in Exp 6b)."));
C.push(P("**Quarantined runs.** The first pass of the Exp 2 write runs is invalid: the charger was unplugged and the lid closed, and the Mac slept repeatedly during the runs (`pmset` log), producing single writes of up to 180 s. The 42 files are kept untouched in `data/raw/invalid_sleep_2026-10-22/`, excluded from all results, and the runs were repeated under the guards above."));

// ---------- 2 Exp 1
C.push(H1("2. Exp 1: zero-queue baselines (QD1)"));
C.push(LAB("Hypothesis.", "4 KiB random read 60 to 90 µs; 4 KiB random write 20 to 60 µs and faster than read; 128 KiB sequential read 70 to 150 µs; 128 KiB sequential write 80 to 200 µs; p99 at 1.5 to 3 times p50."));
C.push(tcap("Exp 1 results. Fixed: QD1, 1 job, 32 GiB range, direct I/O. Varied: workload. Mean (sd) over 3 trials."));
C.push(table(DATA.exp1, [3.2, 1.3, 1, 1.6, 1.6, 1.6, 1.6], { numeric: true, firstColBold: true }));
C.push(sp());
C.push(...fig("fig1_baseline_qd1.png", 4.8, fcap("Exp 1: QD1 latency percentiles (log scale, µs) and throughput (MB/s). Fixed: QD1, 1 job. Varied: workload.")));
C.push(LAB("Result.", "Random read (54.6 µs) is below the predicted range and random write (80.9 µs) is **slower** than read, the opposite of the prediction. Sequential read matches (134.9 µs, 970 MB/s). Sequential write is far below the range (29.1 µs per 128 KiB). The random-read tail is much tighter than predicted (p99/p50 = 1.16); random-write p99 is 2.6 times p50, as predicted."));
C.push(LAB("Interpretation.", "*Inferred:* a QD1 read costs one flash page read plus controller, encryption, PCIe and kernel time, and nothing overlaps; a 128 KiB read needs 32 pages. A 128 KiB write finishing in 29 µs implies the SSD acknowledges writes from a fast buffer before flash programming. Random 4 KiB writes are slower than reads and have a heavy tail (p99 181 µs), *hypothesis:* because APFS is copy-on-write, so each overwrite allocates blocks and updates metadata, while large sequential writes allocate contiguously. The sequential-write throughput (2.5 GB/s) is partly limited by fio generating 128 KiB of random data per IO outside the measured latency (IOPS x latency gives 0.56), so the throughput understates the device; the latency is unaffected."));

// ---------- 3 Exp 2
C.push(H1("3. Exp 2: block-size sweep"));
C.push(LAB("Hypothesis.", "Read throughput saturates at 5 to 7 GB/s; latency flat to 16 KiB then roughly linear; random approaches sequential from 128 KiB; writes saturate at 2 to 5 GB/s."));
C.push(tcap("Exp 2 results. Fixed: effective QD16 (16 psync jobs), 32 GiB range, direct I/O. Varied: block size, random vs sequential, read vs write. Mean of 3 trials (sd in `data/processed/summary.csv`). A dash means not run."));
C.push(table(DATA.exp2c, [1.1, 1.3, 1, 1.2, 1.1, 1.4, 1, 1.2, 1.1], { numeric: true, firstColBold: true, size: 15 }));
C.push(sp());
C.push(...fig("fig2_blocksize.png", 6.5, fcap("Exp 2: throughput (MB/s), IOPS (log) and mean latency (µs, log) against block size. Fixed: QD16. Varied: block size, pattern, direction. Error bars: sd of 3 trials.")));
C.push(LAB("Result.", "Reads saturate at 10.6 to 12.9 GB/s and writes at 9.3 to 10.7 GB/s, both far above the predicted ranges. Random and sequential differ by only 9% at 4 KiB (778 vs 854 MB/s) and are within noise from 128 KiB. Write IOPS is not monotonic: 4 KiB writes reach 45 to 47 k IOPS while 16 to 64 KiB writes reach 92 to 104 k."));
C.push(LAB("Interpretation.", "*Inferred:* the large-block points are bandwidth-bound, and then latency follows from the queue: 16 x 256 KiB / 12,872 MB/s = 326 µs, the measured 326 µs; 16 x 1 MiB / 12.8 GB/s = 1.31 ms against 1.315 ms measured. 12.9 GB/s exceeds the PCIe 4.0 x4 payload limit (7.9 GB/s), so the link is faster than that. Random equals sequential because flash has no seek cost and direct I/O removes read-ahead. *Hypothesis:* the jump in write IOPS between 4 and 16 KiB suggests a native 16 KiB page, with 4 KiB writes being partial-page operations. Write points of 32 KiB and above show an effective depth of 13.7 to 14.6 rather than 16 (flagged, **measured**): *inferred* to be fio's own per-IO data generation outside the measured latency, so the device sees about 14 outstanding writes. Read points give 16.0."));

// ---------- 4 Exp 3
C.push(H1("4. Exp 3: read/write mix"));
C.push(LAB("Hypothesis.", "Mixed total IOPS below a linear blend of the pure cases; read latency 1.3 to 3 times higher at 50/50."));
C.push(tcap("Exp 3 results. Fixed: 4 KiB random, QD16, 32 GiB range. Varied: read share. Mean of 3 trials; latencies are mean / p99 in µs per operation type."));
C.push(table(DATA.exp3, [1, 1.1, 1.1, 1.5, 1, 1.5, 1.5], { numeric: true, firstColBold: true }));
C.push(sp());
C.push(...fig("fig3_rwmix.png", 4.8, fcap("Exp 3: IOPS and mean latency by operation type against read/write mix. Fixed: 4 KiB random, QD16. Varied: read share.")));
C.push(LAB("Result.", "Read mean latency at 50/50 is 2.5 times the pure-read value (72 to 179 µs) and read p99 rises 12 times (108 to 1330 µs). Total IOPS is far below the arithmetic blend (135 k at 50/50) but equals the time-weighted blend: 1 / (0.5/220.4 k + 0.5/49.4 k) = 80.7 k predicted against 81.0 k measured, and 108 k against 112.3 k at 70/30."));
C.push(LAB("Interpretation.", "*Inferred:* a read costs about 4.5 µs of device time and a write about 20 µs, and a mix averages those costs, so no extra interference penalty is needed to explain throughput. Interference shows in the tail instead: reads queue behind slow writes in the shared 16-deep queue. Write mean latency drops in a mix (215 µs at 50/50 against 323 µs pure) because fewer writers are in flight (about 9 by IOPS x latency)."));

// ---------- 5 Exp 4
C.push(H1("5. Exp 4: queue-depth sweep and the knee"));
C.push(LAB("Hypothesis.", "IOPS rises about linearly to QD8 to 16, saturates at 180 to 250 k, knee (smallest depth reaching 90% of peak IOPS) at QD8 to 32, latency then grows as depth divided by peak IOPS."));
C.push(P("The sweep was run twice, early (A) and again about 54 minutes later (B), because the identical workload had given two different speeds (Section 10)."));
C.push(tcap("Exp 4 results, 4 KiB random read, 32 GiB range. Fixed: direct I/O, 20 s runs. Varied: effective queue depth, engine, run (A early, B later). Mean of 3 trials. The check IOPS x mean latency matched the configured depth within 1% for every psync point and within 2.1% for every posixaio point."));
C.push(table(DATA.exp4c, [0.7, 1.2, 1.3, 1.3, 1.2, 1.3, 1.3, 1.4], { numeric: true, firstColBold: true, size: 15 }));
C.push(sp());
C.push(...fig("fig4_qd_sweep.png", 6.4, fcap("Exp 4: IOPS against mean latency (left, log x) and the effective-depth check (right). Fixed: 4 KiB random read. Varied: queue depth 1 to 256, engine, run A or B. Ringed points are the knee (QD16). Error bars: sd.")));
C.push(LAB("Result.", "Peak IOPS is 189.9 k (A) and 222.7 k (B). The knee by the stated rule is **QD16** in both runs: `psync` QD16 reaches 98.5% of A's peak and 98.7% of B's, while QD8 reaches only 57% and 60%. Past the knee latency is proportional to depth: 256 / 189.4 k = 1.351 ms against 1.347 ms measured (A) and 256 / 220.6 k = 1.160 ms against 1.154 ms (B)."));
C.push(LAB("Little's law is a check here, not an explanation.", "In a closed-loop fio run each of N workers issues its next IO only after the previous one completes, so IOPS x mean latency equals N nearly by construction. Its value is as a validity check that the effective queue depth is real: it confirms that `psync` with `numjobs=N` and `posixaio` with `iodepth=N` (up to 256) keep N IOs outstanding, and it shows when they do not (`psync` with `iodepth=64` gives 1.00 because a synchronous engine collapses to QD1, Section 8). It says nothing about why throughput stops growing."));
C.push(LAB("The knee comes from saturation (inferred).", "Evidence: (1) IOPS rises almost linearly to QD8 (7.6 times the QD1 rate), bends at QD16 (13.1 times) and is flat from QD64 to QD256 (A: 189.9 k, 189.3 k, 189.4 k; B: 214.1 k, 222.7 k, 220.6 k) while latency grows with depth; (2) two different submission mechanisms end at the same ceiling, so it is not one engine's overhead (`psync` is faster below QD32, 187 k against 151 k at QD16 in A, *hypothesis:* because `posixaio` hands each IO to a small kernel thread pool); (3) the limit is not interface bandwidth: the same drive moves 12.9 GB/s with 256 KiB reads at only 49 k IOPS, against 0.78 GB/s at 190 k IOPS for 4 KiB, so the 4 KiB ceiling is a per-command limit (controller command rate, flash parallelism and the host kernel path); (4) fio uses about 2.2 of the 18 cores' worth of CPU, so the host is not out of CPU. **Not established:** how the ceiling splits between controller, firmware and host path. The 17% shift between the two machine states (Section 10) shows the ceiling is not a pure device property."));

// ---------- 6 Exp 5
C.push(H1("6. Exp 5: tail latency"));
C.push(LAB("Hypothesis.", "At mid depth (QD4) p99 is 1.5 to 2.5 times p50 and p99.9 is 3 to 8 times p50; the spread is wider at the knee."));
C.push(tcap("Exp 5 results, 4 KiB random read, 60 s runs. Fixed: direct I/O, 32 GiB range. Varied: queue depth (4 mid, 16 knee). Mean (sd) over 3 trials; latencies in µs."));
C.push(table(DATA.exp5, [1.3, 0.8, 1, 1, 1, 1, 1, 1.1, 1.1, 0.9, 0.9], { numeric: true, firstColBold: true, size: 14 }));
C.push(sp());
C.push(...fig("fig5_tail_latency.png", 4.2, fcap("Exp 5: latency percentiles (µs, log scale) at QD4 and QD16, with IOs per run. Fixed: 4 KiB random read, 60 s. Varied: queue depth. Error bars: sd of 3 trials.")));
C.push(LAB("Result.", "There are 3.3 M IOs per run at QD4 (about 3,300 samples above p99.9) and 11.3 M at QD16 (about 11,300). p99/p50 is 1.43 at QD4 and p99.9/p50 is 2.2, well below the predicted 3 to 8 times: the tail is tighter than expected. The knee run's slightly larger p99.9/p50 (2.39) is within one sd of p99.9 (23 to 34 µs), so no claim is made. p99.99 rests on only 300 to 1,100 samples per run and its sd (430 to 480 µs) is more than half its mean (670 to 840 µs), so it is reported but not interpreted."));
C.push(LAB("Interpretation.", "*Inferred:* moderate-depth reads have few interference sources (no writes, no garbage collection), so the tail is mostly queueing: from QD4 to QD16, p50 rises 18% (70 to 83 µs) and p99 32% (100 to 133 µs). The 6 to 13 ms maxima are rare outliers, *hypothesis:* OS scheduling or controller housekeeping. This experiment ran in the slower machine state."));

// ---------- 7 Exp 6
C.push(H1("7. Exp 6: working set and device state"));
C.push(LAB("Hypothesis.", "A 1 GiB range matches the 32 GiB range within 10% (reads) and 20% (writes). Sustained writes burst at 4 to 6 GB/s and may drop after cache exhaustion (about 50% chance)."));
C.push(P("**6a, address range (4 KiB random, QD16, 3 trials).** Reads: 189.1 k IOPS on 1 GiB against 189.6 k on 32 GiB (0.3% apart). Writes: 46.9 k against 47.8 k (1.8%). The hypothesis holds with a much smaller gap than allowed. *Inferred:* flash read and program costs do not depend on the logical range, and mapping-cache capacity is not limiting at 32 GiB."));
C.push(tcap("Exp 6b: sustained sequential write, one run. Fixed: 1 MiB blocks, 4 jobs, direct I/O, stop at 2.2 TB or 300 s. Throughput from 1 s log windows."));
C.push(table(DATA.exp6b, [4, 3], { firstColBold: true }));
C.push(sp());
C.push(...fig("fig6_working_set_and_sustained_write.png", 6.5, fcap("Exp 6: IOPS for 1 GiB and 32 GiB ranges (left, 3 trials, error bars sd); sustained write throughput in GB/s over time with SMART temperature (middle) and against bytes written (right). Fixed: 4 KiB QD16 (6a) and 1 MiB 4 jobs (6b). Varied: address range (6a), time (6b).")));
C.push(LAB("Result and caveat.", "No cliff was observed. Throughput fell from 12.6 GB/s in the first second to about 11.0 GB/s by 10 to 15 s (a 13% initial burst effect) and stayed there for the rest of the 198 s run and 2.2 TB (slowest 1 s window 8.96 GB/s; last 30 s 11.04 GB/s against 10.99 GB/s for 10 to 60 s). Also checked: p99.9 write latency 4.0 ms and maximum 19.6 ms (no stalls), temperature (up to 65 °C with no throughput change) and fio against SMART byte counts. **This is a single run, and the absence of a cliff reflects the limits of the test (the drive was never filled, and the 2.2 TB went to one 32 GiB logical range), not proof that no SLC-style cache exists.** *Hypothesis:* APFS copy-on-write sends new blocks to the SSD while old ones are trimmed, so the drive always had free blocks; exposing a cliff would need the drive to be filled, which the 20% free-space rule forbids. The byte cap replaced a 300 s-only plan that would have written about 3.3 TB at the measured rate."));

// ---------- 8 Exp 7
C.push(H1("8. Exp 7: misleading setup (page cache and wrong queue depth)"));
C.push(LAB("Hypothesis.", "Buffered reads show 1 to 5 µs and 50 to 300 times the IOPS of direct reads; `psync` with `iodepth=64` behaves like QD1."));
C.push(tcap("Exp 7 results, 4 KiB random read on a 1 GiB range. Fixed: bs 4 KiB, 20 s + 5 s ramp. Varied: setup A to D. Mean (sd) over 3 trials."));
C.push(table(DATA.exp7, [3.6, 1.6, 1.4, 1.4, 0.9, 1.3], { numeric: true, firstColBold: true }));
C.push(sp());
C.push(...fig("fig7_misleading_setups.png", 6.5, fcap("Exp 7: IOPS (log), mean latency (log) and effective depth (log) for setups A (direct, QD1, correct), B (buffered, QD1, page cache), C (direct, QD16, correct) and D (`psync` with `iodepth=64`). Varied: setup. Error bars: sd.")));
C.push(LAB("Result and mechanism.", "Buffered reads (B) give 1.32 M IOPS at 0.69 µs, **90.6 times** the IOPS and 99 times lower latency than the correct direct run (A: 14.5 k IOPS, 68.6 µs). That is 5.4 GB/s of \"reads\" from a drive whose real QD1 random-read rate is 60 MB/s, and it is 6 times the best real 4 KiB rate (223 k IOPS, C). *Measured:* with the same file and job and only `direct` changed, the data come from RAM. *Inferred:* buffered `pread` hits the unified buffer cache and never reaches the NVMe queue. The latency is below the predicted 1 to 5 µs because fio recorded a minimum of 0 ns, so many hits complete faster than its timer resolves (*inferred*). Setup D is identical to A (14,395 against 14,540 IOPS) and its effective depth is 1.00 against 64 configured: the number in the job file is not the depth the device saw."));

// ---------- 9 scorecard
C.push(H1("9. Hypothesis scorecard"));
C.push(P("Predictions are in `HYPOTHESES.md`, committed before data collection with two dated amendments (also before any experiment data); they were not edited afterwards.", { keepNext: true }));
C.push(tcap("Predictions scored against results."));
C.push(table([["Exp", "Prediction", "Outcome"],
  ["1", "4K random read 60 to 90 µs", "Missed low in Exp 1 (54.6 µs); in range in the other machine state (68.6 to 70.1 µs)"],
  ["1", "4K random write faster than read", "**Wrong** (80.9 vs 54.6 µs)"],
  ["1", "128K sequential read 70 to 150 µs", "Hit (135 µs)"],
  ["1", "128K sequential write 80 to 200 µs", "Missed (29 µs)"],
  ["2", "Read plateau 5 to 7 GB/s", "Missed (10.6 to 12.9 GB/s)"],
  ["2", "Write plateau 2 to 5 GB/s", "Missed (9.3 to 10.7 GB/s)"],
  ["2", "Random approaches sequential from 128K", "Hit (and within 9% at 4K)"],
  ["3", "Mix total below linear blend", "Hit, but explained by time-weighting, not interference"],
  ["3", "Read latency 1.3 to 3 times at 50/50", "Hit (2.5 times mean, 12 times at p99)"],
  ["4", "Saturation 180 to 250 k IOPS, knee QD8 to 32", "Hit (189 k and 223 k, knee QD16)"],
  ["4", "Effective depth matches configured within 5% (psync)", "Hit (within 1%)"],
  ["4", "posixaio stays near depth 16", "Withdrawn in Amendment B (true only on macOS 26.5.2)"],
  ["5", "p99.9 is 3 to 8 times p50", "Missed (2.2 to 2.4 times)"],
  ["6a", "Range within 10% (read), 20% (write)", "Hit (0.3%, 1.8%)"],
  ["6b", "Burst 4 to 6 GB/s, possible cliff", "Burst far higher (11.7 GB/s over 10 s); no cliff"],
  ["7", "Buffered 50 to 300 times the IOPS", "Hit (90 times)"],
  ["7", "`iodepth` ignored by `psync`", "Hit (effective depth 1.00)"]], [0.6, 4.2, 5.4], { size: 16 }));
C.push(sp());

// ---------- 10 anomalies
C.push(H1("10. Anomalies"));
C.push(P("**1. Two performance levels for an identical workload.** 4 KiB random read at 16 `psync` jobs gave 187 to 192 k IOPS in Exp 2, 4, 5, 6a and 7, and 215 to 224 k IOPS in Exp 3, a drift check, a 30-run time series and the Exp 4 replicate (Figure 8). The difference is visible at QD1 too (55.6 µs against 70.1 µs mean), so it is not only thread placement at saturation. In the high level fio's kernel CPU use is about 262% of a core against about 209% (**measured**; a consequence, not a cause). **Analysis of existing data only, no new runs:** the 57 runs of this workload (15 low, 42 high) form four consecutive episodes (low 19:32, high 22:32, low 22:43 to 23:13, high 23:21 to 23:38), so each factor is effectively tested on four episodes."));
C.push(tcap("Factors tested against the two IOPS levels (57 runs, existing metadata). r is the point-biserial correlation with the level."));
C.push(table(DATA.state_split.slice(0, 9).map((r) => r.map((c) => c.replace(/ \(consequence, not cause\)/, " (consequence)"))), [3.2, 2, 2, 2.3], { size: 15 }));
C.push(sp());
C.push(...fig("fig8_state_drift.png", 5.8, fcap("Every run of the identical workload (4 KiB random read, 16 psync jobs, 32 GiB range) against time, coloured by experiment (left), and IOPS against fio system CPU (right). Fixed: workload. Varied: time of run.")));
C.push(P("Power source: AC for all 57 runs, so there is no variation to explain anything. Sleep: none during any run. Thermal: SMART temperature exists only at stage boundaries, the ranges overlap between levels, and no per-run reading exists, so there is no evidence either way. Display on: 12 of 15 low runs against 42 of 42 high runs, a weak proxy for user activity. Run order correlates (r = +0.68) only through the episode layout. The strongest association is the volume written in the 30 minutes before the run (r = +0.92: mean 2,136 GB before high runs, 308 GB before low runs), but it is confounded with run order and one episode contradicts it: Exp 4's QD16 runs at 22:43 were low although 1.5 TB had been written about 12 minutes earlier. **Conclusion: no single factor accounts for the split; recent write volume is the only candidate that lines up, and it is an untested hypothesis.** Other **untested hypotheses:** a storage or SoC power or clock state; macOS placement of fio threads on performance or efficiency cores; background system activity. **Consequence:** absolute numbers from different experiments carry about 17% uncertainty; comparisons within one experiment hold."));
C.push(P("**2. Invalid Exp 2 write runs:** the Mac slept during the first pass (Section 1); quarantined and repeated. **3. OS upgrade mid-project:** macOS 26.5.2 to 27.0.1 raised `kern.aiomax` from 90 to 1024 and `kern.aioprocmax` from 16 to 256, so the first conclusion that `posixaio` is capped at 16 became wrong; the engine check was repeated and `HYPOTHESES.md` amended (Amendment B) before any experiment data. **4. Writes show an effective depth of 13.7 to 14.6** at 16 jobs: fio's data generation sits outside the measured latency. **5. 4 KiB writes have half the IOPS of 16 KiB writes:** *hypothesis:* partial-page writes. **6. Exp 3 and 4 SMART read delta is 1.55 times fio's count** against about 1.15 expected from ramp time: unexplained."));

// ---------- 11 limitations
C.push(H1("11. Limitations"));
for (const t of [
  "One machine, one file, one filesystem. Controller, FileVault encryption, APFS copy-on-write and OS cache layers cannot be disabled, so \"SSD performance\" means file-on-APFS performance.",
  "`F_NOCACHE` direct I/O is not a durability test (no `F_FULLFSYNC`): write latencies are acknowledgements from the device buffer and say nothing about power-loss behavior.",
  "macOS has no blktrace or Linux-style `iostat`. Observable: fio latency histograms, SMART counters, `pmset` logs, per-process CPU. Not observable: controller-internal queue depth, per-run SSD temperature, PCIe link state, garbage-collection or SLC state, and `F_NOCACHE` at syscall level.",
  "fio runs at most about 16 jobs here, so `psync` depths stop at 16; deeper depths use `posixaio`, whose latency includes thread hand-off overhead.",
  "The sustained write is one run and never filled the drive. Exp 2 write runs are 4 s short-window means; Exp 6b is the steady-state check and agrees with their plateau.",
  "The two machine states (Section 10) limit absolute cross-experiment comparison to about 17%."]) C.push(B(t));

// ---------- 12 ceilings
C.push(H1("12. Interface and device ceilings against measured"));
C.push(tcap("Roofline-style summary. Measured values from `data/processed/summary.csv`; PCIe payload ceilings are public specification values (link generation assumed, not read)."));
C.push(table(DATA.ceilings, [3, 3.2, 4], { firstColBold: true }));
C.push(sp());
C.push(...fig("fig9_roofline_summary.png", 4.8, fcap("Measured throughput (GB/s) against PCIe x4 payload ceilings. Fixed: direct I/O, 32 GiB file. Varied: workload.")));
C.push(P("*Inferred:* 12.9 GB/s exceeds PCIe 4.0 x4 (7.9 GB/s), so the drive uses a Gen5-class or Apple-specific link, and reads reach 82% of a Gen5 x4 payload ceiling, so a link-bound read ceiling is plausible. Small reads are IOPS-bound, not bandwidth-bound: 4 KiB at 190 to 223 k IOPS uses about 6 to 7% of the read bandwidth."));

// ---------- 13 team and AI
C.push(H1("13. Team Contributions and AI Use"));
C.push(P("Claude Code (model Sonnet 5.5) generated most of the code and the first-draft text of this report. The students are responsible for validating the measurements, interpreting the results and defending the claims in the sections they own; they do not claim to have written the code. Details of what Claude Code produced, the errors it made and how they were corrected are in Appendix A (`AI_USE.md`)."));
C.push(tcap("Ownership of results (target split) and Claude Code's role."));
C.push(table([["Role", "Owner", "Scope", "What they validate and defend"],
  ["Student A", "[STUDENT TO FILL: name]", "Safety guards, preconditioning, Exp 1 (QD1 baselines), Exp 2 (block size)", "Reviews every guard in the scripts, confirms the direct I/O verification, defends the latency table"],
  ["Student B", "[STUDENT TO FILL: name]", "Exp 3 (read/write mix), Exp 4 (queue-depth sweep), knee analysis, Little's law check", "Explains the knee from device and interface saturation and why Little's law is a validity check here"],
  ["Student C", "[STUDENT TO FILL: name]", "Exp 5 (tail latency), Exp 6 (device state, working set), Exp 7 (misleading setup), anomalies including the 189 k against 222 k split, sustained-write caveat", "Defends the tail, device-state and anomaly sections and the limits of the sustained-write result"],
  ["Joint", "All three", "Hypotheses and their scoring; section edits for owned experiments; each student's own AI-use paragraph; final consistency pass", "Final consistency pass owner: [STUDENT TO FILL: name]"],
  ["Claude Code", "AI tool", "Generated fio job files, run and parse scripts, plotting code; drafted `REPORT.md` and this document; proofreading and consistency checks; flagged anomalies and errors in its own earlier work (for example the invalid sleep-affected Exp 2 write runs)", "Not a substitute for student validation; parser checked by hand against raw fio JSON and every table generated from the CSVs"]],
  [0.9, 1.5, 4, 3.6], { firstColBold: true, size: 15 }));
C.push(sp());
for (const s of ["A", "B", "C"]) C.push(P(`**[STUDENT TO FILL: Student ${s} name]: what I changed, tested, or rejected.** [STUDENT TO FILL: what you changed] [STUDENT TO FILL: what you tested independently] [STUDENT TO FILL: what you rejected or corrected and why (at least one concrete item)]`));
C.push(P("**Claude Code.** Generated the job files, scripts, plots and the first drafts of the report and this document, ran the benchmarks through the driver scripts, and found and reported errors in its own earlier work: a stale engine conclusion after the macOS upgrade, sleep-invalidated write runs, shell bugs that made scripts exit silently, and a write-volume estimate that the project owner had to correct. **Independent checks recorded in the repository and data:** direct against buffered latency (87 times, with a stop rule); SMART read and write counters against fio byte counts; quarantine and rerun of the sleep-affected Exp 2 write runs; the `psync` `iodepth=64` check (effective depth 1.00 against 64 configured)."));

// ---------- 14 reproducibility
C.push(H1("14. Reproducibility"));
C.push(P("Everything is in the repository folder `Project-3` (fio job files in `fio/`, drivers and analysis in `scripts/`, untouched fio JSON in `data/raw/`, CSVs in `data/processed/`, figures in `plots/`, `README.md`, `HYPOTHESES.md`, `AI_USE.md`). One command reproduces the full study: `brew install fio smartmontools`, then `bash scripts/run_all.sh`. It waits for AC power, runs the engine check, preconditions the 32 GiB file, runs the direct I/O check (stopping if `direct=1` looks cache-like), then Exp 1 to 7, a drift series and the Exp 4 replicate, and rebuilds tables, figures and `REPORT.md`. Conditions: charger plugged in, lid open, machine idle. A clean run takes about 3 hours and writes about 4 TB; this project's SMART counter recorded about 6.4 TB in total, including invalidated runs and smoke tests. `bash scripts/cleanup.sh` deletes only the test file and marker files."));

// ---------- appendix
C.push(H1("Appendix A. AI use detail (from AI_USE.md)"));
for (const t of [
  "**Generated by Claude Code:** all files under `Project-3/` except the owner's decisions: job files, scripts, `HYPOTHESES.md` and amendments, README, report text and this document. The project owner supplied the experiment list, safety rules and the approvals (install fio and smartmontools, a direct against buffered check before any full run, a 5-minute cap on the sustained write, 3 trials for the tail experiment, correct the write-volume estimate, stage order).",
  "**Write-volume estimate too low (owner correction):** the first estimate of 150 to 300 GiB was far below the real figure, about 6.4 TB for the project, because the drive writes at 10 to 12 GB/s.",
  "**Stale engine conclusion (found by Claude Code from smoke data):** `posixaio` was believed capped at 16; the OS had been upgraded and the limit was 256. The engine check was repeated, the design changed and the change recorded in Amendment B before any experiment data.",
  "**Invalid Exp 2 write runs (found by Claude Code):** the driver checked AC power only at stage start and did not prevent sleep. Per-run power checks, `caffeinate` and a wall-time validity check were added and the runs repeated.",
  "**Shell bugs:** `$rw__bs` parsed as one variable; two `set -e` with `pipefail` bugs (`ps | head`, and `smartctl` returning non-zero on success) made scripts exit silently. A nonsensical phrase in an early draft of `HYPOTHESES.md` was corrected before data were committed.",
  "**Wrong predictions:** writes slower than reads at QD1, a tail tighter than predicted (p99.9 at 2.2 times p50 against 3 to 8 predicted), and read and write bandwidth about 2 times higher than predicted; scored in Section 9 and not adjusted.",
  "**Verification:** parser checked by hand against raw JSON; every table generated from the CSVs; every number in this document was traced to `data/processed`, the raw logs or an explicit formula by `scripts/check_docx_numbers.py` (none untraced; 23 low-precision values were checked by hand; the trace is in `data/processed/docx_number_trace.md`). Not verified: the explanations labeled hypothesis, and the cause of the two performance levels.",
  "**[STUDENT TO FILL: what each team member modified, tested, rejected or re-ran by hand after Claude Code's output, and who contributed what.]** Claude Code cannot know this and has not written it."]) C.push(B(t));

const doc = new Document({
  creator: "Project 3 team", title: "SSD Performance Profiling", description: "ECSE 4320/6320 Project 3 report",
  styles: { default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: FONT, color: "1F3864" }, paragraph: { spacing: { before: 220, after: 90 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, font: FONT, color: "2F5496" }, paragraph: { spacing: { before: 140, after: 60 }, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1008, bottom: 1008, left: 1152, right: 1152 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Project 3: SSD Performance Profiling    |    Page ", size: 16, color: "666666" }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "666666" }), new TextRun({ text: " of ", size: 16, color: "666666" }), new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "666666" })] })] }) },
    children: C }] });
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(ROOT + "/Project3_SSD_Report.docx", b); console.log("wrote Project3_SSD_Report.docx", b.length, "bytes"); });
