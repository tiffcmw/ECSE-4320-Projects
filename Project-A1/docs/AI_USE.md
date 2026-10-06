# AI-use note

## Tool and scope

This project was built in one Claude Code session (model: Claude Sonnet 5.5) working autonomously in phases from the assignment brief. The session produced code, data collection runs, analysis, plots and document drafts. This note says what the AI did, which decisions came from the student, which designs failed, and what the student must still verify personally.

## What the AI generated

- The C harness and benchmarks (`src/*`), the build script, the test file, the Python runner, experiment definitions, analysis and plotting scripts (`scripts/*`).
- The experiment design details (sweeps, parameter ranges, hypotheses with predictions), the plan, the notes files, the report and this README, as first drafts that were then checked against the processed data inside the session (numbers in the report were re-derived from `data/processed/` and corrected where a draft was loose; for example IQR bounds, a pilot-versus-final data citation, the runtime estimate).
- All benchmark runs and placement probes were executed by the AI in the session on the student's machine.

## What the student decided or supplied

- The assignment, the chosen mechanisms and the environment/noise rules (the brief).
- The one decision the AI asked for: after detection showed the chip has Super and Performance cores and no efficiency cores, the student chose to keep the design and reframe it as **Super vs Performance**.
- Whether to approve any `sudo` command: none was needed or requested (`powermetrics` was not used).

Items the student has not yet done (independent testing, parameter changes, interpretation in their own words) are listed in the verification log below and are intentionally not claimed here.

## Flawed-design incidents (built, detected, corrected)

1. **Sequentially linked pointer chase (the required checkpoint).** The plausible design (node i points to node i+1) passed all functional checks and reported 7.8 ns at 1 GB instead of about 108 ns. Detected by the known-answer check and by the per-node cost scaling with stride; diagnosed with disassembly (the loop is a clean dependent `ldr`) and a stride sweep (constant byte rate of about 16.5 GB/s, i.e. the prefetcher). Corrected with a Sattolo random single-cycle permutation. Before data: `data/raw/chase_naive_*.csv`; after data: `data/raw/chase_random_*.csv`; diagnosis: `data/raw/chase_diag_*.csv`, `data/diagnostics/chase_loop_disassembly.txt`; plots: `plots/mech1_latency_naive_vs_random.*`, `plots/ai_resilience_stride_diag.*`. One AI prediction was wrong: that larger strides would defeat the prefetcher.
2. **"Thread QoS is inert."** Pilot probes with one thread on an idle machine, and under a hog, showed no QoS effect. The full sweep showed thread QoS `background` slows and relocates threads when N is 4 or more. A QoS-on-main-thread control (`E2x`) was indistinguishable from the correct design, so only reading the QoS back inside each worker can detect that flaw. The Phase 3 hypotheses were written after the pilots, and say so.
3. **Unsupported explanation in code.** A comment claimed a scalar read kernel was load-slot bound based on one 62 GB/s reading. A rerun showed 97 vs 98 GB/s for scalar vs NEON; the reading was a transient. The comment was corrected.
4. **Accidental run.** A syntax check of `exp_qos.py` imported it and started the full experiment without `caffeinate`. It was killed and its partial output removed before the real run. A command to clean up a scratch clone with `rm -rf` was blocked by the harness safety check and was not worked around; the data-free tree was built with `git archive` instead.
5. **Tooling slips** (not result-affecting): a macOS `sed -i` call needing a suffix, a wrong disassembly match (argument parsing instead of the chase loop), and a plotting call bug, each fixed on detection.

## Known weak points in AI-produced material

- Interpretations that are inferred rather than measured are labeled in the report (SLC size, the 2.6 ns plateau, the cause of the 3.3x background-policy slowdown, why a single background thread stays on Super).
- Two bandwidth points (stride-4 and stride-16 at 1 MB) report rates above the sequential rate and were not validated.
- Phase 3 hypotheses are pilot-informed.
- One fixed random-permutation seed was used; permutation-to-permutation variance was not measured.

## Student verification log

Check each item yourself before submission and tick it.

- [ ] Re-read `docs/ENVIRONMENT.md` and confirm it matches your machine (`sysctl hw.perflevel0.name`, `hw.perflevel1.name`, cache sizes).
- [ ] Run `./build/test_harness` and confirm "all tests passed".
- [ ] Run `QUICK=1 ./scripts/run_all.sh` on your machine (plugged in, Low Power Mode off) and confirm it completes and regenerates plots.
- [ ] Re-run at least one headline measurement yourself and compare: random chase at 1 GB (about 108 ns), naive chase at 1 GB (about 7.8 ns), `taskpolicy -b ./build/qos_loop --kind compute --qos none --reps 2` (about 3x slower than without `taskpolicy`).
- [ ] Open `data/raw/chase_naive_*.csv` and `chase_random_*.csv` and confirm the before/after numbers quoted in the report.
- [ ] Confirm the placement evidence: run `python3 scripts/probe_core_type.py interactive background` and `--wrap "/usr/sbin/taskpolicy -b" none` (needs Xcode) and check the Super/Performance shares.
- [ ] Check every verdict in the report's scorecard (Section 6) against its cited plot or table, and decide whether you agree with "partly supported" calls.
- [ ] Decide whether to validate the two unvalidated bandwidth points or remove them.
- [ ] Rewrite the interpretation sections (3.1 to 3.4, 4.x, 5.x, 7) in your own words and add what you independently concluded; update the "What the student decided" section above to match what you actually did.
- [ ] Confirm no em-dashes remain (`grep -rn "—" . | grep -v build`) and that your name and course details are added where the course requires.
- [ ] Optional: provide a Linux host if you want the `linux/` track; it was not built.
