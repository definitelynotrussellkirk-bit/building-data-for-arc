# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Earlier exposure declaration

Before this visible-only episode I had already reviewed the selected task's
Racket authority and generator, so this is an exposed post-repair solve, not a
blind solve. During this episode I used only `solve/challenge.json`, this work
log, and the visible-example checker; I did not reopen the authority,
generator, reference solutions, or private labels.

## Revision 1

Across all four demonstrations, every nonzero cell is reflected to the row at
`height - 1 - row` in the same column. The destination is filled only when it
is zero. Example 2 is the key precedence witness: the top-right `5` mirrors to
a bottom-right cell already containing `4`, and the output keeps `4` rather
than swapping or overwriting it. Example 4 confirms the same rule with
nonzeros on both halves and an even-height grid.

Implemented a direct immutable overlay: copy the input, then for each zero
cell read its vertically mirrored partner and copy that value when nonzero.
The competing hypotheses “replace the whole grid by its vertical reflection”
and “let the reflected value overwrite conflicts” are rejected by examples 2
and 4. The only remaining uncertainty is masked-query scoring, which the
visible checker intentionally withholds.
