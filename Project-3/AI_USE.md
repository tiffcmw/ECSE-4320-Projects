# AI use note

Tool: Claude Code (model Sonnet 5.5) working inside this repository, driven by the project owner's prompt and approvals.

## What Claude Code generated

Everything under `Project-3/` except the owner's decisions listed below: the fio job files, all `scripts/` (safety guards, drivers, parser, tables, plots, report builder), `HYPOTHESES.md` and its two amendments, `README.md`, `report_src/REPORT.template.md` (and so `report_src/REPORT.md`), this file, and the analysis text. Claude also ran the benchmarks by launching the driver scripts and read the results.

## Decisions that came from the project owner (given in the prompt or in approvals)

- The experiment list, the safety rules, the 32 GiB file size, the 20% free-space rule and the no-sudo rule.
- Approval with changes: install both fio and smartmontools; run a 20 s direct-vs-buffered check before any full run and stop if `direct=1` looks cache-like; cap the sustained write at 5 minutes with the write volume stated up front; run 3 trials (not 5) for the tail experiment; correct the write-volume estimate in the README; the stage order and commit-per-stage rule.

## Things Claude got wrong (found by Claude or by the owner)

1. **Write-volume estimate far too low (owner correction).** Claude first estimated 150 to 300 GiB of write traffic; the owner pointed out it was too low. The real figure is about 6.4 TB for the whole project (README table), because the drive writes at 10 to 12 GB/s, and a 300 s sustained write would have been about 3.3 TB at the measured rate (replaced by a 2.2 TB cap).
2. **Engine conclusions went stale (found by Claude from smoke-test data).** The first engine check said `posixaio` is capped at 16 outstanding IOs and designed the queue-depth sweep around forked processes. The smoke data contradicted this: macOS had been upgraded from 26.5.2 to 27.0.1 between sessions and the limits had changed (`kern.aioprocmax` 16 to 256). The engine check was repeated, the design changed, and a dated amendment to `HYPOTHESES.md` (before any experiment data) records it. A planned negative example ("`posixaio` iodepth 64 is really 16") became false and was replaced by `psync` with `iodepth=64`.
3. **First Exp 2 write results invalid (found by Claude).** The write runs showed single IOs lasting up to 180 s. Claude first suspected the drive, then found in `pmset -g log` that the charger had been unplugged and the Mac slept with the lid closed. The runs were quarantined (`data/raw/invalid_sleep_2026-10-22/`) and repeated. The cause was a gap in Claude's own driver: it checked AC power only once at the start of a stage and did nothing to prevent sleep. Per-run power checks, `caffeinate` and a wall-clock validity check were added.
4. **Shell bugs.** `$rw__bs` in a filename was parsed by bash as one variable (smoke test caught it); two `set -e` plus `pipefail` bugs (`ps | head`, and `smartctl` returning a non-zero status when it works) made the precondition script exit silently with no output, which cost several relaunches.
5. **A nonsensical phrase in `HYPOTHESES.md`.** Claude wrote "128-bit-wide sequential 1 MiB writes"; it was corrected before the file was committed with data.

Not a Claude error but it shaped the schedule: the owner said the charger was plugged in while the machine reported battery power; Claude checked `pmset` and stopped rather than run on battery.

## Hypotheses that were wrong

Several predictions in `HYPOTHESES.md` were missed (writes slower than reads at QD1, tail tighter than predicted (p99.9 at 2.2 times p50 against 3 to 8 predicted), write and read bandwidth 2x higher than predicted); they are listed in the scorecard (Section 9) of `report/Project3_Report.pdf`, not adjusted afterwards.

## Verification done by Claude, and what still needs the team

- Parser checked by hand against raw fio JSON (IOPS, mean latency and Little's-law value match on the engine-check files). Every report table is generated from the CSVs; numbers typed into prose were checked against `data/processed` by `scripts/check_docx_numbers.py` (the untraceable ones are listed in `data/processed/docx_number_trace.md`).
- Not independently verified: the explanations labelled *hypothesis* in the report, and the cause of the two performance levels.

## Team Contributions and AI Use

Claude Code generated most of the code and the first-draft text. The students are responsible for validating the measurements, interpreting the results and defending the claims in the sections they own; they do not claim to have written the code.

| Role | Owner | Scope | What they validate and defend |
|---|---|---|---|
| Student A | Tiffany Cheng | Safety guards, preconditioning, Exp 1 (QD1 baselines), Exp 2 (block size) | Reviews every guard in the scripts, confirms the direct I/O verification, defends the latency table |
| Student B | Marie Morales | Exp 3 (read/write mix), Exp 4 (queue-depth sweep), knee analysis, Little's law check | Explains the knee from device and interface saturation and why Little's law is a validity check here |
| Student C | Alex Redd | Exp 5 (tail latency), Exp 6 (device state, working set), Exp 7 (misleading setup), anomalies including the 189 k against 222 k split, sustained-write caveat | Defends the tail, device-state and anomaly sections and the limits of the sustained-write result |
| Joint | All three | Hypotheses and their scoring; section edits for owned experiments; each student's own AI-use paragraph; final consistency pass | Final consistency pass owner: [STUDENT TO FILL: name] |
| Claude Code | AI tool | Generated fio job files, run and parse scripts, plotting code; drafted `report_src/REPORT.md` and the Word report (final: `report/Project3_Report.pdf`); proofreading and consistency checks; flagged anomalies and errors in its own earlier work (for example the invalid sleep-affected Exp 2 write runs) | Not a substitute for student validation |

**Tiffany Cheng (Student A): what I changed, tested, or rejected.** [STUDENT TO FILL: what you changed] [STUDENT TO FILL: what you tested independently] [STUDENT TO FILL: what you rejected or corrected and why (at least one concrete item)]

**Marie Morales (Student B): what I changed, tested, or rejected.** [STUDENT TO FILL: what you changed] [STUDENT TO FILL: what you tested independently] [STUDENT TO FILL: what you rejected or corrected and why (at least one concrete item)]

**Alex Redd (Student C): what I changed, tested, or rejected.** [STUDENT TO FILL: what you changed] [STUDENT TO FILL: what you tested independently] [STUDENT TO FILL: what you rejected or corrected and why (at least one concrete item)]

**Claude Code.** Generated the job files, scripts, plots and the first drafts of the report and the Word document, ran the benchmarks through the driver scripts, and found and reported errors in its own earlier work: a stale engine conclusion after the macOS upgrade, sleep-invalidated write runs, shell bugs that made scripts exit silently, and a write-volume estimate that the project owner had to correct. **Independent checks recorded in the repository and data:** direct against buffered latency (87 times, with a stop rule); SMART read and write counters against fio byte counts; quarantine and rerun of the sleep-affected Exp 2 write runs; the `psync` `iodepth=64` check (effective depth 1.00 against 64 configured).
