# Blind solve notes — 88b8e6aaa49d

## Visible evidence

All three labelled outputs preserve shape and color counts. Comparing coordinates shows
that each input cell at `(r, c)` moves to `(H - 1 - r, W - 1 - c)`:

- Example 1's top-left `1` becomes the bottom-right `1`, while its bottom-left `0`
  becomes the top-right `0`.
- Applying a 180-degree rotation to every row/order reproduces all three outputs exactly.
- The rule is shape-agnostic, so it directly covers the two rectangular/square queries.

## Revision 1

Hypothesis: rotate the entire grid 180 degrees, implemented by reversing row order and
reversing each row. This is simpler than transpose/reflection alternatives and matches
all visible examples cell-for-cell.

No task-specific generator, canonical rule, reference solution, labels, notes, or audit
evidence were consulted. Before preparation I saw only packet-level workflow/design
documents, not this task's rule or implementation.
