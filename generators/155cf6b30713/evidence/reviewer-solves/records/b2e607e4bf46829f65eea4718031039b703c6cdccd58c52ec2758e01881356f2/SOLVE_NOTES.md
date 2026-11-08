# Solve notes

This is a human work log for the required **exposed** post-repair solve. I had already reviewed the generator family, but during this solve I used only the visible episode printed by `solve prepare`; I did not reopen the generator, Racket rule, reference solution, or hidden outputs.

## Hypothesis

Each input is three equal square panels separated by full-height color-5 columns. Panel 1 is changed into panel 2 by a non-identity square symmetry plus a consistent color substitution. Apply the same symmetry to panel 3, recolor colors demonstrated in panel 1→2, and leave other panel-3 colors unchanged.

Visible checks:

- Example 0 uses a 90° clockwise rotation. The demonstrated map is `7→6`, `8→2`, `4→3`; query color `3` passes through.
- Example 1 uses main-diagonal transpose. The map is `3→7`, `5→6`; query color `6` passes through.
- Example 2 uses vertical reflection. The map is `2→9`, `7→8`, `6→1`; query color `9` passes through.

The examples jointly rule out recoloring every query color and rule out applying color changes without geometry. I implemented exact-position support matching over the seven non-identity D4 transforms, inferred a consistent map, and used identity-on-unmapped colors.

## Predicted query structure

- Query 0: transpose; `3→6`, `5→2`, while query color `2` passes through.
- Query 1: transpose; `6→8`, `2→1`, `4→9`, while query color `8` passes through.
