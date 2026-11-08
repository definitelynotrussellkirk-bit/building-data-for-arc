# Solve work log

Earlier rule exposure: yes. I repaired this generator before this required fresh
visible-only solve. During this solve I did not reopen the generator, Racket rule,
canonical record, reference solution, or private query labels; I used only the
prepared visible examples.

## Hypothesis from visible examples

The background is `0`. Red `2` cells form separate 4-connected components. A
component is transformed only when it is a gapless straight horizontal or
vertical segment with at least two cells. Its two extreme cells become cyan `8`;
interior red cells stay `2`. Bent red components stay unchanged, and the connected
object in the other nonzero color is a distractor that stays unchanged.

Visible checks:

- Example 0 has a two-cell vertical segment and a four-cell horizontal segment;
  all four endpoints become `8`, while the bent red L and color-1 line remain.
- Example 1 confirms a two-cell segment has both cells recolored and that a bent
  red component remains red.
- Examples 2–3 confirm both orientations and longer interiors.

I considered recoloring all degree-one red cells, but the bent controls have such
cells and remain unchanged. I also considered processing every straight object
regardless of color, but the non-red distractors remain unchanged.

## Implementation

Flood-fill every 4-connected red component. If all cells share one row or one
column and fill the complete interval, recolor the two extremes. Otherwise copy
it unchanged. The untouched scaffold first failed with `NotImplementedError`;
this is the first actual solve revision.
