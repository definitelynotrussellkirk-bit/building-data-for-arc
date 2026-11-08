# Solve notes

This is a human-readable work log, not a token-level model trace. I had earlier
rule exposure during generator review, so this attempt is **not blind**. During
the solve phase itself I consulted only `solve/challenge.json`; I did not reopen
the generator, Racket authority, reference solutions, or private labels.

## Visible-example inference

Hypothesis from all three demonstrations:

1. A red `2` on the left edge emits a horizontal red ray to the right.
2. A green `3` on the top edge emits a vertical green ray downward.
3. A maroon `9` blocks a ray and remains unchanged.
4. A cell reached by both rays becomes cyan `8`; a cell reached by only one ray
   takes that ray's color.
5. Cells outside all unblocked rays remain unchanged.

Checks against the visible examples:

- Train example 1 shows a horizontal ray stopping immediately at the blocker in
  row 6 and a longer ray stopping at column 5 in the last row.
- Train example 2 shows both one-direction fills and cyan crossings, while the
  blocker at row 5, column 2 stops the vertical ray below it.
- Train example 3 shows that blockers stop only the ray sharing their row or
  column; unrelated rays continue.

## Revision 1

Implemented the rule directly by copying the input, tracking whether each red
row remains open while scanning left-to-right, and checking each green column
for an earlier blocker. No speculative special cases were added. There were no
failed program revisions before this implementation because the visible
examples distinguish direction, stopping, and intersection behavior directly.
