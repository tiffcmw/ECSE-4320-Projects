# Invalid runs: system slept during the run

All Exp 2 write runs (`randwrite` and `write`, 42 files) from stage `run_02_exp1_exp2.sh` on 2026-10-22.
Cause (from `pmset -g log`): the charger was unplugged at 19:47:46 and the lid closed at 19:47:58 ("Clamshell Sleep");
the Mac then slept and woke repeatedly ("Maintenance Sleep", 6 to 206 s each) during the write runs, which began 19:47:20.
fio reported single-IO latencies of up to 180 s and job runtimes of up to about 200 s for 4 s runs. These are not drive
behaviour. Files are kept untouched as evidence and are excluded from every analysis. The runs were repeated after the
power/sleep guards in `scripts/common.sh` were added (per-run AC check, `caffeinate`, wall-time validity check).
Exp 1 (19:27 to 19:32) and Exp 2 reads (19:32 to 19:47) ran on AC with no sleep events and are kept.
