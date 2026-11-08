# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — translated-copy hypothesis

Earlier exposure before this solve: none. I had not opened this task's generator,
reference rule, private labels, prior solutions, or audit material.

Across all three visible pairs, color 1 forms the same four-cell object and colors
2 and 3 are unique markers. Let `v = position(3) - position(2)`. Translating every
color-1 cell by `v` gives exactly the newly painted color-8 cells:

- example 0: `v=(-1,+1)`;
- example 1: `v=(-1,-5)`;
- example 2: `v=(+5,+1)`.

The output preserves the input and overlays the translated copy in color 8. This
also explains why example 0 loses its visible color-2 cell: one translated cell
lands on it and overwrites it. A competing hypothesis based only on adjacency to
color 3 does not explain the exact shape and displacement in all examples.

I wrote a visible-example regression script before implementation; the stub failed
with `NotImplementedError`, as expected. The implementation now locates all color-1
cells, computes the 2-to-3 displacement, copies the grid, and paints the translated
cells color 8. Remaining uncertainty is limited to malformed inputs (missing or
multiple markers); the visible task consistently has one marker of each color.
