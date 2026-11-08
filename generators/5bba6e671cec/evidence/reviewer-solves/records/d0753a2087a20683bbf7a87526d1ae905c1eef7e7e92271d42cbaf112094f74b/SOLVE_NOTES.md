# Post-repair visible-only solve

This is an authored observation/check summary, not a token-level model trace.
Earlier rule exposure: yes, during the generator review and repair. During this
solve phase the generator, Racket source, previous solutions and private labels
were closed. This is an exposed post-repair solve, not a blind discovery claim.

## Visible observations

All three demonstrations have input 8 rows × 8 columns and output 8 rows × 8
columns. Both query inputs are 8 rows × 8 columns; their outputs are unknown.
Frame colors 4 and 7 remain unchanged in every demonstration. Other colors
are relabeled consistently across all their cells, including disconnected
parts and color 0.

- Example 0 swaps colors 3 and 6.
- Example 1 maps 0→5, 5→8, 8→0.
- Example 2 maps 5→6, 6→1, 1→8, 8→5.

## Implementation and verification

The proposed Python solution averages every coordinate for each non-frame
color, orders those means by angle about the grid center, and shifts the
colors one position clockwise. The angle origin is east; changing that origin
only changes the start of the cyclic ordering. It never uses a color's first
pixel as its location and does not treat zero as background.

Revision 1 is the genuine attempted solution. The official check will record
visible fit and query execution while withholding query correctness. No
deliberately wrong revision was created.
