# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — row-local leftmost-color propagation

Earlier rule exposure: no. I had not opened any generator, canonical rule, solution,
or audit evidence before this attempt.

Observation: in every training row, zero cells stay zero and all nonzero cells are
recolored to the leftmost nonzero color in that same row. This explains the
non-majority row `[3, 0, 0, 1, 1, ...] -> [3, 0, 0, 3, 3, ...]`, which rules out
a majority-color interpretation. Rows with one nonzero value are unchanged, and
empty rows remain empty.

Program: find the first nonzero value in each row, then replace every nonzero cell
in that row by that value. The transformation preserves shape and nonzero support.

Remaining uncertainty: none on the visible examples; the only assumption is that
0 is the background, consistently supported by all examples.
