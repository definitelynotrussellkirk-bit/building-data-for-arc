# Blind solve notes

## Hypothesis

Each input contains a colored motif in the upper-left portion of an even-sized canvas. The output completes bilateral symmetry by copying every nonzero cell to its horizontal reflection, vertical reflection, and combined 180-degree reflection. Colors are preserved and the canvas size does not change.

## Evidence from visible examples

- Example 0: `(0,1)=6` appears additionally at `(0,6)`, `(7,1)`, and `(7,6)`; the entire four-cell color-6 motif is mirrored the same way.
- Example 1: `(0,1)=2` becomes the four positions `(0,1)`, `(0,6)`, `(3,1)`, `(3,6)`, while `(1,3)=6` similarly fills `(1,4)`, `(2,3)`, and `(2,4)`.
- Example 2: every upper-left mark has the same three reflected copies, including distinct colors 3, 4, and 6.

## Implementation

Start with a copy of the input. For every nonzero cell `(r,c)`, write its color at all combinations of rows `r` / `H-1-r` and columns `c` / `W-1-c`. No visible example contains a conflicting color at reflected positions.

## Remaining uncertainty

If a hidden input contains inconsistent prefilled colors at symmetric positions, the intended conflict policy is not inferable from the demonstrations. The generated examples appear to avoid that case.
