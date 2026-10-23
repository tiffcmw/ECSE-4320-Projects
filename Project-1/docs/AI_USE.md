# AI-use note

## Account of who did what
The account below was supplied by the team of three students and is the authoritative statement of authorship.
- Each of the three students wrote one kernel together with its correctness testbench and its benchmark.
- The fourth kernel was written jointly by all three students.
- The students set the experimental expectations before the measurements and cross-checked the results.
- Claude Code (Anthropic's command-line agent) helped with plotting, analysis, proofreading and optimizing the code. No other AI tool was used for code or text in this project.

## The flawed-benchmark incident (Experiment 8)
Planned part (`src/naive/naive_bench.c`, `plots/exp8_naive_vs_fixed.png`): a naive benchmark was written first on purpose, with a corrected twin. N1: a multiply loop in the same translation unit with an unused result was optimised away (0 ns, infinite GiB/s; fixed: 263 GiB/s). N3: first-touch page faults inside the timed region gave 81 GiB/s instead of 148. N2 (zero-page reads) did not reproduce and is reported as a failed prediction.

Unplanned flaws found during development, before or during measurement (each one changed the methodology):
1. The first "fixed" N2 benchmark still timed 0 ns for every run. A plain `asm volatile("" ::: "memory")` barrier does not prevent hoisting calls that read memory that never escaped; the pointer had to be passed to the asm. Both datasets are kept (`data/raw/naive_phase5_run1_fix_still_hoisted.csv`, `data/raw/naive_phase5.csv`). It was caught because the run printed infinite bandwidth for the variant that had been labelled correct.
2. `restrict` was written on local pointers inside the kernel; the disassembly showed runtime overlap checks, because clang derives `noalias` only from parameters. The kernels were restructured (`vecreports/VECTORIZATION.md`). The early smoke data (`data/raw/smoke_phase1*.csv`) were produced with the flawed version and are kept for the record; no plot uses them.
3. The default `-fno-vectorize` baseline is not unrolled, so the first SIMD speedups (about 5x) were inflated. Found from a smoke run; an unrolled scalar baseline was added and made primary.
4. The plan said "long double accumulation"; on arm64 macOS `long double` is 64-bit, so the reference was changed to double-double.
5. `-Rpass=loop-vectorize -Rpass=slp-vectorizer` as two separate options: the second replaced the first, so the first vectorization-report run contained no vectorization remarks. Found by comparing the table with the disassembly.
6. Register-by-register annotations for the stencil assembly were written without tracing them; they were removed and replaced with what the listing shows.
7. A hypothesis that the smoke data had already contradicted was disclosed in a dated section of `docs/HYPOTHESES.md`, not edited.

Found during the final revision: the first draft of the chase analysis assumed that the 1 MiB latency step is a TLB effect; the page-granular test refuted that (HA6) and the cause is reported as unknown. A harness build had been left broken by an unfinished earlier edit (a test source file listed in the build but absent); it was completed (`tests/test_extra.c`) and the tests were run before any data collection.

## Where the predictions were wrong
Recorded in `docs/HYPOTHESES.md` (verdict column). Examples: alignment penalty (predicted under 5%, measured up to 45%), SIMD gain compressing at L2 and DRAM (it compresses at L1), dot product not vectorized (it is, in order), fast-math dot speedup 2x to 4x (measured 10x to 14x, mostly from independent accumulators), an SLC step (none seen), the 1 MiB latency step as a TLB effect (refuted), read-only as the fastest pattern (slowest), the stride-32 spike as a one-line-per-access threshold (refuted).

## Student verification log (confirm each personally before submission)
- [ ] Run `scripts/run_all.sh` on the student's own machine: tests must pass and all plots regenerate. Optionally `COLLECT=quick scripts/run_all.sh` (about 20 minutes, plugged in, Low Power Mode off).
- [ ] Check `docs/REPRODUCTION.md` (clean-clone result) against a fresh clone.
- [ ] Disassemble one kernel and compare with `vecreports/VECTORIZATION.md`: `objdump -d --disassemble-symbols=_kern_saxpy_f32_auto build/obj/auto/saxpy_f32.o` (after `scripts/build.sh`), and `clang -O3 -Rpass=loop-vectorize ...` as in `scripts/vecreport.py`.
- [ ] Spot-check three numbers in `report/Project1_Report.pdf` against `data/processed/` and the raw CSVs (for example the 2.08x f32 SAXPY L1 speedup, the 147 GiB/s ceiling, 3.99 fmla per cycle). A spot-check log kept during development is not a substitute.
- [ ] Read the hypotheses table and confirm each outcome matches its cited evidence; confirm with `git log --follow docs/HYPOTHESES.md` that hypotheses were committed before the data (addendum 4 in `032af85`, HA6 in `9733d53`).
- [ ] Confirm the machine state during the runs claimed: AC power, Low Power Mode off (`pmset -g`), no heavy background apps (`docs/ENVIRONMENT_sessions.log` shows the load averages; a video player was running in `ext1`).
- [x] Powermetrics samples were run by a student (see above).
- [ ] Each student confirms that the account of who wrote which kernel, testbench and benchmark (top of this file) is accurate, and that it matches what the course requires to be disclosed.
- [ ] Confirm the unexplained items in Section 6 (Anomalies and unresolved items) of the report are acceptable, or investigate one.
- [ ] Confirm that skipping SME is acceptable (SME exists on this chip; not used).
- [ ] Check the course policy on AI-assisted proofreading and plotting, and edit the report if it requires more than the disclosure above.
- [ ] Check that no em-dashes appear: `grep -rn $'\xe2\x80\x94' . --include='*.md' --include='*.py' --include='*.sh' --include='*.c' --include='*.h'` should print nothing.
- [ ] Check that `Project-A1/` was not modified: `git log --stat -- Project-A1` shows no commits from this project.
