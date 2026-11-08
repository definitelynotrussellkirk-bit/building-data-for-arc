# Solve work log

## Prior exposure

Before this blind solve I had not opened task `9a1459fe40d0`'s generator, Racket rule,
reference solutions, private labels, audit records, or earlier solution explanations.
I used only the public examples printed by `solve_episode.py blind prepare`.

## Revision 1 — occupancy XOR after reflection

Each input has a full-height vertical color-8 divider with equal-width halves.
Ignoring object colors, I reflected every occupied cell in the left half across the
divider into right-half coordinates. The output's color-7 cells are exactly the
symmetric difference between that reflected left occupancy mask and the original
right occupancy mask:

- a location occupied on only one side becomes 7;
- a location occupied at corresponding positions on both sides cancels to 0;
- all other cells, the divider, and the entire left half are 0.

I checked this manually against all three visible examples. For example 1, reflected
left cells at `(4,9)` and `(6,9)` overlap right-side cells and disappear; the six
non-overlapping positions are exactly the six output 7s. Example 2 likewise cancels
`(2,7)` and `(2,12)` and retains the eight remaining one-sided positions.

The implementation locates the unique all-8 divider, verifies equal-width halves,
then emits 7 wherever reflected-left occupancy XOR right occupancy is true. Colors
other than 0 are treated only as occupancy, matching the examples where paired
positions cancel even when their colors differ.

Remaining uncertainty before the public check: whether unseen inputs ever contain
an additional full-height 8 column or unequal halves. The visible task presentation
strongly indicates a single central divider, so the solver rejects malformed cases
rather than guessing.
