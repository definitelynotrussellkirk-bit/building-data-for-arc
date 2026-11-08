# Solve work log

## Exposure declaration before solving

I had not opened the blind task's generator, canonical rule, notes, solutions,
audit records, or private labels. I had read only the packet-level instructions,
the assignment duties, and `solve-blind/challenge.json`.

## Revision 1 — perfect-square repacking

**Hypothesis.** The most frequent colour is background. Every other colour has
perfect-square multiplicity and represents a solid square. The output discards
excess background and repacks the squares by increasing side length, from left
to right, bottom-aligned, with exactly one background column between squares.

**Evidence from the visible examples.**

- Example 1 has non-background counts 1, 4, and 16. Its output contains a 1x1,
  2x2, and 4x4 block in that order, separated by one column and bottom-aligned.
- Example 2 has non-background counts 4 and 9. Its output contains a 2x2 then a
  3x3 block with the same alignment and spacing.
- Example 3 has non-background counts 1, 9, and 16 and exactly repeats the first
  arrangement with different colours.
- Both test inputs preserve those count signatures. The second is a horizontal
  reflection of the third training geometry, which suggests the output depends
  on colour areas rather than source position.

**Implementation.** Count colours, choose the modal colour as background,
validate every remaining count as a square, sort `(side, colour)`, allocate a
canvas of height `max(side)` and width `sum(side) + number_of_gaps`, and paint
all blocks against the bottom edge.

**Alternatives considered.** I briefly considered an unfolding or object-motion
rule tied to input orientation, but exact preservation of every non-background
count and the canonical size-sorted output in all three examples makes direct
area repacking substantially simpler and better supported.

**Remaining uncertainty.** Tied square sizes are not shown. Sorting by colour is
used only as a deterministic tie-break; no visible example depends on it.
