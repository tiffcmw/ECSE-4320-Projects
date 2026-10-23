# Work split (Project 2, three students plus Claude Code)

Team notes. Names are placeholders: replace [Member A], [Member B], [Member C] with the real names. Each student owns the experiments and report sections below and must be able to explain every number in them, including how it was computed from the raw data.

| Owner | Experiments and sections | Review items | Must be able to explain |
|---|---|---|---|
| [Member A] latency and locality | Exp 1 zero-queue baselines, Exp 2 pattern and granularity (including the non-power-of-two and jittered stride tests), Exp 5 working-set sweep, core placement check | R3 stride aliasing, R9 frequency cross-check, R12 the 2.6 ns plateau, R15 Exp 1 caveats | why the chase is one random cycle, how the level edges are read from the curve, how cycles are derived from the frequency estimate, what the plateau tests exclude and what they do not |
| [Member B] bandwidth and concurrency | Exp 3 read/write mix, Exp 4 intensity sweep, loaded latency, knee, Little's Law | R1 peak bandwidth and percentages, R4 knee definitions, R10 zero versus random data and dc zva, R11 read-only ceiling tests, R13 mixed versus read-only | how N = BW x latency / 128 B is derived and what the single-core plateau of about 19 lines means, why two knee definitions are reported, why random data is the headline for writes |
| [Member C] misses, TLB and pitfalls | Exp 6 kernels and AMAT model, Exp 7 TLB, Exp 8 pitfalls | R2 set aliasing in Exp 7, R7 counters attempt, R14 sibling-project claim removal | why the TLB penalty is paged_rand minus packed, what the counter attempt did and did not return, the AMAT model terms and where it fails |
| All three | R5 amendment table (each owns and signs off the rows for their experiments), R8 rounds and statistics, limitations section, final proofreading, AI-use note placeholders (each fills their own part) | | |
| Claude Code | Scaffolding and fixes in the benchmark and plotting code, reruns approved by the team, numeric consistency script (R17), figure regeneration, report assembly into DOCX and PDF, proofreading | | Claude Code proposes verdicts with the evidence; the owning student confirms or changes each verdict |

## Cross-review (reviewer reproduces one headline number from the raw data with the provided scripts)

| Reviewer | Reviews | Headline number reproduced | Reviewed by (name, date) |
|---|---|---|---|
| [Member A] | [Member B] experiments and text | [STUDENT TO FILL: which number, which command] | [STUDENT TO FILL] |
| [Member B] | [Member C] experiments and text | [STUDENT TO FILL] | [STUDENT TO FILL] |
| [Member C] | [Member A] experiments and text | [STUDENT TO FILL] | [STUDENT TO FILL] |

Commands to reproduce from the stored raw data without re-measuring: `scripts/parse.py && scripts/validate.py && scripts/plot.py && scripts/check_report.py` from the Project-2 folder. Headline numbers appear in `data/processed/tables.md`.

## Sign-off per amendment row (R5)

| Amendment (report table) | Owner | Confirms the amended wording and reason |
|---|---|---|
| H2b, H2c stride design | [Member A] | [STUDENT TO FILL] |
| H2f stride aliasing | [Member A] | [STUDENT TO FILL] |
| H12 plateau tests | [Member A] | [STUDENT TO FILL] |
| H3e content dependence, H4f knee, H11 ceiling tests | [Member B] | [STUDENT TO FILL] |
| H7d TLB layout controls, H13 counters | [Member C] | [STUDENT TO FILL] |
