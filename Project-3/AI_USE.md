# AI use note

Tool: Claude Code (model Sonnet 5.5) working inside this repository, driven by the project owner's prompt and approvals.

## What Claude Code generated

Everything under `Project-3/` except the owner's decisions listed below: the fio job files, all `scripts/` (safety guards, drivers, parser, tables, plots, report builder), `HYPOTHESES.md` and its two amendments, `README.md`, `REPORT.template.md` (and so `REPORT.md`), this file, and the analysis text. Claude also ran the benchmarks by launching the driver scripts and read the results.

## Decisions that came from the project owner (given in the prompt or in approvals)

- The experiment list, the safety rules, the 32 GiB file size, the 20% free-space rule and the no-sudo rule.
- Approval with changes: install both fio and smartmontools; run a 20 s direct-vs-buffered check before any full run and stop if `direct=1` looks cache-like; cap the sustained write at 5 minutes with the write volume stated up front; run 3 trials (not 5) for the tail experiment; correct the write-volume estimate in the README; the stage order and commit-per-stage rule.

## Things Claude got wrong (found by Claude or by the owner)

1. **Write-volume estimate far too low (owner correction).** Claude first estimated 150 to 300 GiB of write traffic; the owner pointed out it was too low. The real figure is about 6.4 TB for the whole project (README table), because the drive writes at 10 to 12 GB/s, and a 300 s sustained write would have been about 3.7 TB (replaced by a 2.2 TB cap).
2. **Engine conclusions went stale (found by Claude from smoke-test data).** The first engine check said `posixaio` is capped at 16 outstanding IOs and designed the queue-depth sweep around forked processes. The smoke data contradicted this: macOS had been upgraded from 26.5.2 to 27.0.1 between sessions and the limits had changed (`kern.aioprocmax` 16 to 256). The engine check was repeated, the design changed, and a dated amendment to `HYPOTHESES.md` (before any experiment data) records it. A planned negative example ("`posixaio` iodepth 64 is really 16") became false and was replaced by `psync` with `iodepth=64`.
3. **First Exp 2 write results invalid (found by Claude).** The write runs showed single IOs lasting up to 180 s. Claude first suspected the drive, then found in `pmset -g log` that the charger had been unplugged and the Mac slept with the lid closed. The runs were quarantined (`data/raw/invalid_sleep_2026-10-22/`) and repeated. The cause was a gap in Claude's own driver: it checked AC power only once at the start of a stage and did nothing to prevent sleep. Per-run power checks, `caffeinate` and a wall-clock validity check were added.
4. **Shell bugs.** `$rw__bs` in a filename was parsed by bash as one variable (smoke test caught it); two `set -e` plus `pipefail` bugs (`ps | head`, and `smartctl` returning a non-zero status when it works) made the precondition script exit silently with no output, which cost several relaunches.
5. **A nonsensical phrase in `HYPOTHESES.md`.** Claude wrote "128-bit-wide sequential 1 MiB writes"; it was corrected before the file was committed with data.

Not a Claude error but it shaped the schedule: the owner said the charger was plugged in while the machine reported battery power; Claude checked `pmset` and stopped rather than run on battery.

## Hypotheses that were wrong

Several predictions in `HYPOTHESES.md` were missed (writes slower than reads at QD1, tail 2 to 3x tighter than predicted, write and read bandwidth 2x higher than predicted); they are listed in the scorecard of `REPORT.md`, not adjusted afterwards.

## Verification done by Claude, and what still needs the owner

- Parser checked by hand against raw fio JSON (IOPS, mean latency and Little's-law value match on the engine-check files). Every report table is generated from the CSVs; numbers typed into prose were checked against those tables.
- Not independently verified: the explanations labelled *hypothesis* in the report, and the cause of the two performance levels.
- **[STUDENT TO FILL]** What the owner modified, tested, rejected or re-ran by hand after Claude's output, and which parts each team member contributed. Claude cannot know this and has not written it.
