# Visible-only solve notes

This is a human-authored work log from the three displayed training examples.
I had studied the selected family earlier while repairing its generator, so this
is **not** a blind solve. During this solve I did not reopen the generator,
canonical Racket rule, reference solutions, private labels, or prior solve
explanations.

## Observations

- The modal color is unchanged background.
- Each non-background color forms one logical icon. Missing cells are added in
  the same color; no existing cell is removed.
- Square footprints are completed under quarter-turn rotation. Example 0's
  color-9 icon gains the absent right-side quarter-turn partners.
- Rectangular footprints use horizontal/vertical reflection around a rounded
  center, with the shorter side's box expanded when needed. This explains the
  color-5 and color-7 completions in example 2.
- Some pieces that are separate under 8-connectivity belong to one icon when
  they face each other across exactly one background cell in a cardinal
  direction. They must be merged before measuring bounds.
- Odd square centers are a special case: the center is filled when the completed
  icon supplies the displayed local support. The larger visible chiral square
  suggests a diagonal-support case in addition to the simple four-cardinal
  support case.

## Implemented hypothesis

1. Find the modal background.
2. Extract 8-connected foreground components.
3. Repeatedly merge components separated by one cardinal background cell.
4. For each merged icon, use its bounding box:
   - square: fill missing quarter-turn partners;
   - rectangle: fill horizontal/vertical reflection partners in the rounded-
     center odd box.
5. For an odd square whose center remains blank, fill it when either all four
   cardinal neighbors are present or, for a 7x7-or-larger icon, all four
   diagonal neighbors and four side midpoints are present.

The implementation reads symmetry partners from the original input so newly
painted cells do not invent extra evidence. I am checking this single coherent
hypothesis against all visible examples before stopping.
