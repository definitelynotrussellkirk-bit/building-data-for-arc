# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — complete hollow orthogonal crosses

Earlier exposure: none to this task's generator, rule, reference solution, private
labels, or prior solve notes. I inspected only the prepared visible examples.

Hypothesis: each changed cell is a zero at the center of a plus-shaped arrangement
whose four orthogonal neighbors all have the same nonzero color. The output fills
that center with the shared color and leaves all other cells unchanged.

Evidence from the visible pairs:
- Example 0 fills `(2, 1)` because its up/down/left/right neighbors are all `6`.
  The nearby cross centered at `(1, 11)` is already nonzero (`7`), so it is not
  overwritten.
- Example 1 fills centers `(4, 7)` and `(10, 4)`, both surrounded by four `7`s.
- Example 2 fills `(1, 1)` and `(4, 7)` with `1`, and `(1, 7)` with `5`.

Implementation choice: scan interior zero cells and read neighbors from the
original grid, writing matches into a copied grid. This makes multiple fills
simultaneous and avoids a newly filled center influencing another detection.

Predicted query changes: query 0 fills `(2, 10)` with `5`; query 1 fills `(1, 1)`
with `5`. The colored center `6` at query-1 coordinate `(3, 4)` stays unchanged
although four `2`s surround it, matching the non-overwrite behavior in example 0.

Remaining uncertainty: the visible examples do not distinguish one simultaneous
pass from repeated closure, but a single simultaneous pass is the minimal rule
and exactly accounts for every demonstrated change.
