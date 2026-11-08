# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit evidence, or prior solution notes. I used only the visible
examples printed by `python3 review.py blind prepare` and the files in this
visible-only solve directory.

## Revision 1 — modal non-background color

**Observation.** Every output preserves the 4×4 shape and becomes a solid color.
In examples 1 and 2, that color is the most frequent input color. Example 0 is
the discriminating case: color 0 occurs six times, but the output is color 5,
which occurs five times. This suggests color 0 is background and the selected
color is the most frequent nonzero color.

Input nonzero count rankings:

- example 0: 5×5, 6×3, 2×1, 3×1 → fill with 5;
- example 1: 4×6, 6×4, 3×3, 8×1 → fill with 4;
- example 2: 3×8, 5×5, 2×1, 4×1, 9×1 → fill with 3.

**Program.** Count all cells, remove color 0 when at least one nonzero color is
present, choose the highest-count remaining color, and return an input-shaped
solid grid. For an otherwise unspecified tie, retain first-appearance order as
a deterministic fallback. For an all-zero grid, fill with 0.

**Query predictions.** Query 0 should be a 4×4 grid of color 6 (six cells versus
five color-2 cells). Query 1 should be a 4×4 grid of color 2 (seven cells versus
six color-8 cells).

**Alternatives considered.** The output color could have been the global mode,
but example 0 rejects that because 0 is globally most frequent. It could also
have been selected by a geometric property, but the same simple count rule
matches all three examples and the examples appear deliberately constructed
with a dominant and runner-up nonzero color plus singleton distractors.

**Remaining uncertainty.** The examples do not specify behavior on ties or on an
all-zero input. Those cases are handled deterministically but are not claimed as
part of the inferred task rule.
