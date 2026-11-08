# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: I had not seen this task's generator, rule, notes, solutions, audit records, or private query labels. I used only the displayed visible examples.

Hypothesis: each nonzero color forms one object/trace, and the output lists the colors of the three largest objects by number of occupied cells, from largest to third-largest. Visible counts support this exactly:

- Example 0: 9→9 cells, 3→8, 1→7, then 5→6, 4→5, 6→4; output is `[9, 3, 1]`.
- Example 1: 7→14, 5→11, 1→7, 2→4; output is `[7, 5, 1]`.
- Example 2: 7→21, 2→15, 1→10, 6→6, 5→3; output is `[7, 2, 1]`.

I first added `test_solution_visible.py`, which reads only `challenge.json`; it failed on the provided `NotImplementedError` as expected. The implementation counts all non-background cells per color and emits the top three as a 3×1 grid. Remaining uncertainty: visible examples do not specify tie handling, but all demonstrated object sizes are distinct.
