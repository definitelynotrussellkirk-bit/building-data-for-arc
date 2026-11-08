# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — row-confinement hypothesis

Earlier exposure: I had not opened this task's generator, rule, reference solution,
private labels, prior solve notes, or the assigned repair target. I used only the
public grids printed by `blind prepare` / `solve-blind/README.md`.

Observation: every retained nonzero color occupies cells in exactly one row of the
input. This includes singleton colors. Every erased color appears in two or more
rows. The criterion explains all visible examples independently of cell count,
contiguity, row length, or whether multiple retained colors occur in different rows.

Program: collect the set of row indices occupied by each nonzero color, retain a
color iff that set has cardinality one, and replace every other nonzero cell with
background 0. Shape and retained positions are unchanged.

Predicted queries: query 0 retains colors 2 and 4; query 1 retains 7, 3, 6, and 2.
The main remaining uncertainty is whether a hidden case intends a different but
visible-equivalent description, although the supplied queries exercise singleton,
short, and longer one-row colors against distractors spanning multiple rows.
