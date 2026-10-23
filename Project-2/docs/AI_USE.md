# AI-use note

## What Claude Code generated
Placeholder to be confirmed by the student after review: Claude Code (model claude-sonnet-5-5) generated the C harness (`src/`), the run, parse and plot scripts (`scripts/`), `docs/` and `report/` drafts, and `hypotheses.md`, from a task description supplied by the student. It also designed the experiments and the substitutes for tools missing on macOS.

## What I modified
[STUDENT TO FILL: specific edits you made to code, parameters, or text]

## What I tested or verified myself
[STUDENT TO FILL: runs you reproduced, numbers you spot-checked, commands you ran yourself]

## What I rejected or changed after review
[STUDENT TO FILL: suggestions you refused, claims you removed, results you did not trust]

## Incidents where Claude Code's own work was wrong (found and corrected during the work)
1. Read kernels used a single XOR accumulator chain, capping single-thread read bandwidth at about 73 GB/s at every cache level. Found by Claude Code from a flat bandwidth curve; fixed; two earlier data sessions are superseded (`hypotheses.md` amendments).
2. Stride sweeps kept the byte footprint fixed, which shrank the number of distinct lines at large strides (cache-resident artifact). Fixed.
3. The loaded-latency probe thread slept during warm-up and lowered its own clock. Fixed.
4. The first delay-injection range was too weak. Raised.
5. Several figures quoted in the first report draft did not match the final session's tables (for example a `dc zva` ratio and TLB values); they were checked against `data/processed/tables.md` and corrected.

## Disclosures made by Claude Code during the work
See the report (`report/Project2_Report.pdf`), Appendix A and Sections 11 to 13. Development smoke tests were run before data collection; benchmarks were not tuned to match hypotheses.
