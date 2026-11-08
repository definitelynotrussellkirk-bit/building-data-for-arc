# Solve work log

## Exposure declaration

I had already inspected and repaired this task's generator and canonical rule
before this required post-repair episode, so this is **not blind**. During the
solve episode itself I used only the visible challenge presentation and my own
Python implementation; I did not reopen the generator, Racket rule, reference
solutions, private labels, or previous solution explanations.

## Revision 1 — largest red 4-component

Across all three visible demonstrations, the only changed cells are color 2
(red) becoming color 8. Treating edge-adjacent red cells as an object gives
three objects per example. In each example the changed object has five cells;
the untouched red objects have fewer cells. The changed object appears first,
middle, and last in scan order across the demonstrations, so position is not the
criterion. The non-red distractor is always preserved.

Hypothesis: find all 4-connected color-2 components, select the one with maximum
cell count, and recolor all its cells to 8 while copying everything else.

Implementation: iterative flood-fill over color 2, then `max(..., key=len)` and
recolor in a deep copy. This handles arbitrary rectangular visible/query grids
and does not depend on the distractor's color or location.

Remaining uncertainty before checking: the visible examples all have a unique
largest component, so maximum ties are unspecified; the generated challenge
appears constructed to avoid that ambiguity.
