# Fresh solve notes

## Exposure declaration

I had earlier exposure to the task's rule while reviewing the generator before this solve episode. During the solve episode itself, I read only `solve/challenge.json`; I did not consult the generator, Racket rule, reference outputs, or private labels.

## Visible-example inference

All four demonstrations contain one color-9 anchor. For every nonzero, non-9 input cell at offset `(dr, dc)` from that anchor, the output places the same color at offset `(-dr, -dc)`. The input-side source cells are erased, the anchor remains, and all other cells are zero. The examples include one-sided shapes, cells on the anchor row/column, disconnected cells, and differently colored cells occupying opposite positions, which distinguish point reflection from horizontal-only, vertical-only, copy-and-reflect, and empty-destination-only shortcuts.

## Implementation

`solution.py` finds the unique 9, constructs a blank same-sized grid, preserves the anchor, and point-reflects every other colored cell. It rejects malformed inputs with a missing/duplicate anchor or an out-of-bounds reflection rather than silently clipping.
