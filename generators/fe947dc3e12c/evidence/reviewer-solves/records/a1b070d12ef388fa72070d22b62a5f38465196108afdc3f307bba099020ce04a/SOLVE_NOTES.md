# Solve work log

## Exposure declaration

Before this solve I saw only the packet-level instructions and the visible examples produced by `blind prepare`. I did not open this task's generator, Racket rule, canonical record, private labels, prior solution notes, or any repair/audit target source.

## Revision 1 hypothesis

Each grid contains exactly three nonzero 4-connected objects. The output preserves every object's cells and the zero background, but replaces the object's original color according to its area rank:

- largest object -> color 1
- smallest object -> color 2
- remaining (middle-sized) object -> color 4

Evidence from the visible training pairs:

- Example 0 object areas are 6, 5, and 4, mapped to 1, 4, and 2.
- Example 1 uses one input color for all objects, with areas 7, 3, and 2, again mapped to 1, 4, and 2.
- Example 2 object areas are 7, 5, and 2, again mapped to 1, 4, and 2.

The two queries also have three objects with distinct areas (6/4/2 and 5/3/2), so no tie policy is needed for these visible instances. I will test a solver against all three visible training pairs before checking the episode. Remaining uncertainty: the examples do not determine behavior for ties, diagonal touching, or a number of objects other than three.
