# Visible-example solve notes

This is a human work log for the exposed post-repair solve. I had already seen
the task rule while repairing the generator, so this episode is not blind. During
this solve phase I opened only `solve/challenge.json`; I did not reopen the
Racket rule, generator, retained labels, or previous solution text.

## Hypothesis from the visible examples

The zeros partition the input into a rectangular array of equal framed cells.
Each frame has a dominant/common interior color. Other interior colors act as
markers at a fixed local position within a cell.

For each non-common color and each local interior position independently:

- if that color occurs in two or more cells of the same cell-row, fill that
  local position in every cell between the leftmost and rightmost occurrence;
- if it occurs in two or more cells of the same cell-column, fill every cell
  between the topmost and bottommost occurrence;
- preserve separators, frames, original markers, and unrelated positions.

The examples require both directions and more than one marker color, so a
horizontal-only, vertical-only, or single-color rule is insufficient.

## Implementation choice

The solver discovers separator rows/columns rather than assuming a fixed grid
size. It finds the uniquely modal interior color, then applies the same span
operation at every local interior offset. It reads anchors only from the input,
so newly filled cells do not create an unintended second wave.
