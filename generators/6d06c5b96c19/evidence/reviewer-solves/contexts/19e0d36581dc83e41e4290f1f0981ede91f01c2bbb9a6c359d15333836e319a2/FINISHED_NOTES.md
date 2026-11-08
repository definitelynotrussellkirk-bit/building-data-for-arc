# Solve work log

## Exposure declaration

I had already reviewed this task's generator and rule before entering the
post-repair solve lane, so this is **not blind**. During this solve attempt I did
not reopen the generator, Racket source, reference solutions, private query
labels, or prior solution explanations; I used only the prepared visible
examples.

## Revision 1

Observed that every output has the same number of rows but one fewer column, and
its multiset of cells is exactly the input with column 0 removed. Column 0 is
therefore an instruction strip rather than payload.

The unique red `2` in that strip gives a zero-based row index:

- Example 0: red at row 0; removing column 0 without reordering matches output.
- Example 1: red at row 9 of 10; output payload rows are input rows 1..9 followed
  by row 0, which is a downward cyclic rotation by 9 (equivalently up by 1).
- Example 2: red at row 1 of 6; output starts with the last payload row and then
  rows 0..4, exactly a downward rotation by 1.

Implemented: remove column 0, then cyclically rotate payload rows downward by
the red row index. The examples distinguish this from “move the marked row to
an edge” because the whole row sequence rotates with wraparound.

Remaining uncertainty is limited to malformed inputs; the solution explicitly
requires a rectangular grid and exactly one red cue in column 0.
