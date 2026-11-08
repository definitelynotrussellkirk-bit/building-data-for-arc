# Solve notes

## Visible evidence

All three demonstrations retain the colored 3×3 block in the upper-left and the vertical gray divider. Every blue cell to the right disappears and is replaced by an exact copy of that 3×3 block. The blue cell occupies the center position of the copied block. Orientation and colors are unchanged.

This is visible in examples with multiple row/column locations, including markers not confined to one fixed 3-spaced lattice. The transformation applies independently to every marker and preserves unrelated cells.

## Hypothesis

1. Read rows 0–2 and columns 0–2 as the template.
2. Find every input cell of color 1.
3. For each marker at `(r, c)`, copy the template into rows `r-1..r+1` and columns `c-1..c+1`.
4. Keep the original template, divider, background, and all other cells unchanged.

## Implementation choice

The solver first snapshots all marker coordinates so newly copied colors cannot affect marker discovery. It copies the input before writing and guards boundaries, although every visible marker already admits the full 3×3 stamp.

## Exposure declaration

I had already inspected the generator and canonical behavior during the assigned repair. During this solve episode I used only the visible examples displayed by `solve prepare`; I did not reopen or consult the Racket rule, generator source, private labels, or earlier solution explanations.
