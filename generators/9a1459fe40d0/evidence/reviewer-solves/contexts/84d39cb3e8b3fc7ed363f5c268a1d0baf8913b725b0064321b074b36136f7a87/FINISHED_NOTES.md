# Solve work log

## Exposure

Before this solve I had not opened the task's generator, Racket rule, reference
solution, private labels, audit records, or any earlier explanation. I used only
the visible examples printed by `python3 review.py blind prepare` and the local
`challenge.json` containing the same public examples.

## Hypothesis

Every grid has a full-height central column of color 8, splitting equal-width
left and right panels. Colors other than 0 and the divider act only as occupied
marks; their identities do not matter. Reflect the left panel horizontally onto
the right panel, compare occupancy cell by cell, and draw color 7 where exactly
one side is occupied (symmetric difference/XOR). Clear the left panel, divider,
and all matched cells.

Checks against the demonstrations:

- Example 0: reflected-left and right marks overlap at `(2, 9)` and `(4, 13)`;
  those disappear, while the six non-overlapping positions become 7.
- Example 1: overlaps at `(2, 7)` and `(4, 10)` disappear; the remaining six
  positions match the output.
- Example 2: overlaps at `(1, 9)` and `(2, 7)` disappear; the eight remaining
  positions match the output.

## Implementation and uncertainty

`solution.py` locates the unique all-8 divider, requires equal-width panels,
reflects each left coordinate to the corresponding right coordinate, and emits
7 for occupancy XOR. The main remaining uncertainty is whether a hidden episode
could use a noncentral divider or a nonzero color as background; neither occurs
in the visible examples, and the equal-panel construction is strongly supported.
