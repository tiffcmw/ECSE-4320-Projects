# AI-use note

## Tools
Claude Code (Anthropic CLI agent; the session ran on the model Sonnet 5.5) working in this repository from a single detailed task prompt from the student. No other AI tool was used for code or text in this project.

## What the AI generated
- All code: kernel template, harness, correctness tests, accuracy tool, FMA-peak generator, naive-benchmark demo (`src/`, `tests/`), build and experiment scripts (`scripts/*.sh`), analysis and plotting scripts (`scripts/*.py`).
- All documents in `docs/`, `vecreports/VECTORIZATION.md`, `report/REPORT.md` and `README.md` (first and only drafts, written from the measured data in this repository).
- The experiment designs, hypothesis texts and the numeric predictions in `docs/HYPOTHESES.md`. The assignment text fixed which experiments to do; the AI chose sizes, strides, offsets, thresholds and predicted values.
- It ran all builds and benchmarks itself on the student's machine, and read the plots.

## What the student did, modified, tested or rejected
This section must be completed by the student; the AI cannot attest to what the student did. Fill in below (delete the placeholders):
- Modified: [student to list any code, text or numbers changed by hand]
- Independently tested: [student to list, see the verification log below]
- Rejected or redirected: [student to list suggestions not accepted]
- Decisions made by the student during the session: the task prompt itself (scope, phases, controls, "ASK" rules). No question was put to the student during execution; the SME decision was resolved by the default the prompt specified (SME skipped as non-trivial). powermetrics was not run by the AI (needs sudo); the student ran it afterwards and the AI used the pasted output.

## The flawed-benchmark incident (Experiment 8)
Planned, deliberate part (`src/naive/naive_bench.c`, `plots/exp8_naive_vs_fixed.png`): a naive benchmark was written first on purpose, with a corrected twin. N1: a multiply loop in the same translation unit with an unused result was optimised away (0 ns, infinite GiB/s; fixed: 263 GiB/s). N3: first-touch page faults inside the timed region gave 81 GiB/s instead of 148. N2 (zero-page reads) did not reproduce, and that is reported as a failed prediction.

Unplanned flaws the AI introduced and then found, all before or during measurement (each one changed the methodology):
1. The first "fixed" N2 benchmark still timed 0 ns for every run. A plain `asm volatile("" ::: "memory")` barrier does not prevent hoisting calls that read memory that never escaped; the pointer had to be passed to the asm. Both datasets are kept (`data/raw/naive_phase5_run1_fix_still_hoisted.csv`, `data/raw/naive_phase5.csv`). I only caught it because the run printed infinite bandwidth for the variant I had labelled correct.
2. `restrict` was written on local pointers inside the kernel; the disassembly showed runtime overlap checks, because clang derives `noalias` only from parameters. Found while reading the first disassembly; the kernels were restructured (`vecreports/VECTORIZATION.md`). The Phase 1 smoke data (`data/raw/smoke_phase1*.csv`) were produced with the flawed version and are kept only as pilot data; no plot uses them.
3. The assignment-defined `-fno-vectorize` baseline is not unrolled, so the first SIMD speedups (about 5x) were inflated. Found from a smoke run; an unrolled scalar baseline was added and made primary.
4. The plan said "long double accumulation"; on arm64 macOS `long double` is 64-bit, so the reference was changed to double-double.
5. `-Rpass=loop-vectorize -Rpass=slp-vectorizer` as two separate options: the second replaced the first, so the first vectorization-report run contained no vectorization remarks and the summary table showed "no" for everything vectorized. Found by comparing the table with the disassembly.
6. The AI wrote register-by-register annotations for the stencil assembly without tracing them; they were removed and replaced with what the listing shows (commit "remove untraced register-level claims").
7. A hypothesis in `docs/HYPOTHESES.md` that the pilot data had already contradicted was disclosed as pilot data in a dated section, not edited.

## Where the AI's predictions were wrong
Recorded in `docs/HYPOTHESES.md` (verdict column). Examples: alignment penalty (predicted under 5%, measured up to 40%), SIMD gain compressing at L2/DRAM (it compresses at L1), dot product not vectorized (it is, in order), fast-math dot speedup 2x to 4x (measured 10x to 14x).

## Student verification log (confirm each personally before submission)
- [ ] Run `scripts/run_all.sh` on your own machine: tests must pass and the 15 plots regenerate. Optionally `COLLECT=quick scripts/run_all.sh` (about 10 minutes, plugged in, Low Power Mode off).
- [ ] Check `docs/REPRODUCTION.md` (clean-clone result) matches what you see when you clone the repository fresh.
- [ ] Disassemble one kernel yourself and compare with `vecreports/VECTORIZATION.md`: `objdump -d --disassemble-symbols=_kern_saxpy_f32_auto build/obj/auto/saxpy_f32.o` (after `scripts/build.sh`), and `clang -O3 -Rpass=loop-vectorize ...` as in `scripts/vecreport.py`.
- [ ] Spot-check three numbers in `report/REPORT.md` against `data/processed/exp1_key_table_phase3.csv` and the raw CSVs (for example the 2.08x f32 SAXPY L1 speedup, 150 GiB/s plateau, 3.99 fmla per cycle).
- [ ] Read the hypotheses table and confirm each verdict matches the cited evidence; confirm hypotheses were committed before results (`git log --follow docs/HYPOTHESES.md`; first commit precedes all data).
- [ ] Confirm the machine state during the runs you want to claim: on AC power, Low Power Mode off (`pmset -g`), no heavy background apps. The AI could not enforce the last point; `docs/ENVIRONMENT_sessions.log` shows load averages of 1.2 to 2.4.
- [x] powermetrics: the student ran it three times after the experiments (`data/raw/powermetrics_sample_20261006.txt`, idle; `data/raw/powermetrics_during_benchmark_20261006.txt`, separate terminal during an f32 SAXPY run; `data/raw/powermetrics_during_benchmark_combined_20261006.txt`, one combined command, three samples); the AI read all of them. Result: the Super cluster ran the benchmark at 4608 MHz per busy core (cluster averages 4548 to 4596 MHz), the thread migrated among the six Super cores, and the 4.587 GHz estimate lies inside the measured range. Only one benchmark (f32 SAXPY, 32 MiB) was sampled.
- [ ] Confirm you accept the unexplained items listed in section 10 of the report, or investigate one.
- [ ] Confirm that the SME skip is acceptable (SME exists on this chip; not used).
- [ ] Rewrite or edit the report in your own words as your course policy requires, and complete the "student did" section above.
- [ ] Check there are no em-dashes: `grep -rn $'\xe2\x80\x94' . --include='*.md' --include='*.py' --include='*.sh' --include='*.c' --include='*.h'` should print nothing.
- [ ] Check that Project-A1/ was not modified: `git log --stat -- Project-A1` shows no commits from this project.
