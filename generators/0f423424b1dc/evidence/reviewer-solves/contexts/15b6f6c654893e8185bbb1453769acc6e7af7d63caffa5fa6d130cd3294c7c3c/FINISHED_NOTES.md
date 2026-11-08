# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, reference solution, private labels,
prior solve notes, or any task-specific records for task `0f423424b1dc`. I used
only `solve-blind/challenge.json` and the visible-example checker.

## Revision 1 — unobstructed equal-color segments

**Observation.** In every changed training region, two cells of the same nonzero
color lie in one row or one column and the output fills the zero cells strictly
between them with that color. Examples include the vertical `4,3` pair in the
first lesson and the independent `8`, `2`, and `5` columns in the second.

**Disambiguating counterexample.** The third lesson has two `1` cells in one
column, but a `7` lies between them. The output does not fill either zero gap.
This rules out unconditional endpoint connection and suggests that the whole
open segment must contain only zeros. Singletons and differently colored aligned
cells are unchanged.

**Program.** Group nonzero cells by color. When a color occurs exactly twice,
connect it only when its endpoints share a row or column and every strict
intermediate cell is zero in the original input. Use the original input for all
clearance tests and write into a copy.

**Predicted tests.** Test 1 receives vertical `4` and `7` segments. Test 2 receives
vertical segments for `8`, `3`, and `1`; the singleton `9` and `4` remain unchanged.

**Remaining uncertainty.** The visible examples do not specify crossings between
two newly drawn segments or colors with more than two occurrences. The program
conservatively requires exactly two endpoints and never overwrites an original
nonzero cell.
