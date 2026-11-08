# Post-repair solve notes

This is a human work log. I had already seen the task family while repairing the
assigned generator, so this episode is **exposed**, not blind. During this solve I
read only `solve/challenge.json`; I did not reopen the generator, Racket source,
canonical ledger, reference solutions, or private labels.

## Visible-example analysis

The changed cells are all zeros with equal nonzero immediate horizontal
neighbours:

- `4 0 4 -> 4 4 4` and `6 0 6 -> 6 6 6` in training example 1.
- The last row of example 2 independently fills `3 0 3` and `2 0 2`.
- Example 3 shows overlapping motifs: `3 0 3 0 3` and `7 0 7 0 7` fill both
  zero centers. This indicates simultaneous tests against the original row.

Visible negatives rule out nearby alternatives:

- `4 0 0 4` and `7 0 0 7` stay unchanged, so the rule does not fill an
  arbitrary span between repeated colors.
- Unequal endpoint pairs such as `7 0 3` stay unchanged.
- Vertically aligned same-color cells do not trigger; orientation is horizontal.
- Existing nonzero cells are preserved.

## Hypothesis and implementation

For every row and every non-edge column, if the original cell is 0 and its
immediate left and right neighbours are the same nonzero color, copy that color
into the center. Apply all such replacements simultaneously by reading from the
input and writing to a deep copy.

One implementation revision was needed; no diagnostic or intentionally wrong
submission was made.
