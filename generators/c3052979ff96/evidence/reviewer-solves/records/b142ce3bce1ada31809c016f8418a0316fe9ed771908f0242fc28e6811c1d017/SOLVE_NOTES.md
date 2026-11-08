# Solve notes

The visible pairs have one cyan (8) object, one maroon (9) pivot, and one isolated control value in 1..4. The output preserves the scene and stamps a red (2) copy of the cyan cells after rotating their offsets around the pivot.

Observed code map from the visible examples:
- 1: identity. Examples 1 and 3 replace the cyan cells themselves with red.
- 2: 90 degrees clockwise. In example 2, offset `(-4,+1)` becomes `(+1,+4)`.
- 4: 90 degrees counter-clockwise. In example 0, offset `(-6,-2)` becomes `(+2,-6)`.
- 3 is therefore the remaining half-turn; the first query visibly uses it.

All unrelated colors remain unchanged. A transformed cell is painted red; targets outside the canvas are ignored defensively.
