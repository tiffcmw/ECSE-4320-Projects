## Appendix F. AI-use note

**What Claude Code generated.** The assistant was Claude Code (model claude-sonnet-5-5) running in the terminal on the student's machine, working from the assignment text and instructions supplied by the team. In plain terms it generated: the C benchmark program and its self-tests; the experiment driver, parsing, validation and plotting scripts; the numeric consistency check; the drafts of the analysis text, the hypothesis list and the report assembly; and the choice of substitutes for tools that do not exist on macOS (for example the loaded-latency harness in place of Intel MLC). It also proposed the experiment designs and the interpretation of each result. It ran the benchmarks on the team's machine.

**Errors made by the assistant and corrected during the work.** The read kernels first used a single accumulator chain and capped single-thread read bandwidth; the stride sweeps first shrank the number of distinct lines at large strides; the loaded-latency probe first slept during warm-up and lowered its own clock; the first write kernels stored uniform or zero-filled lines, which made stores look faster than random data allows; and several numbers in earlier drafts did not match the data tables. Section 9 describes each in context.

**What the students modified.** [STUDENT TO FILL: specific edits to code, parameters or text, per member]

**What the students tested or verified themselves.** [STUDENT TO FILL: runs reproduced, numbers spot-checked, commands run, per member]

**What the students rejected or changed after review.** [STUDENT TO FILL: suggestions refused, claims removed, results not trusted, per member]

**Limits of this note.** The assistant cannot know what the students did outside its sessions, so no statement about the students' own work is made here.
