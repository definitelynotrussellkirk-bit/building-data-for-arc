# Solve work log

## Exposure declaration before solving

I had not opened task `52ac31926856`'s generator, Racket rule, notes, prior
solutions, private labels, or audit records. I used only `challenge.json` and my
own scripts over that file.

## Revision 1 — falling liquid and leaky vessels

The single color-1 cell appears above one or more color-2 vessel-like row bands.
The output removes that source cell. A vessel is a rectangular cavity bounded by
continuous color-2 side walls; it holds liquid only when its bottom is solid
between those walls. The source column selects the cavity it falls through.
Open-bottom cavities leak, so the liquid continues to lower bands. The first
closed aligned cavity is filled with color 1. If none is closed, the liquid
reaches the grid floor and fills the bottom row.

Visible evidence:

- Training 0 has one closed cavity spanning columns 4–7 under source column 5;
  its 2x2 interior is filled.
- Training 1's upper aligned cavity has a bottom gap, while the lower aligned
  cavity spanning columns 3–8 is closed; only the lower interior is filled.
- Both aligned vessels in training 2 have a bottom gap, so the final row fills.

I considered choosing the nearest U-shape solely by outline, but training 1
requires leak-through. I also considered flood-filling all geometrically enclosed
zeros, but the source column and gravity order are essential. The implementation
splits color-2 rows into vertical bands, enumerates continuous side-wall pairs,
requires a solid bottom, chooses the narrowest pair containing the source column,
and processes bands from top to bottom.

A small visible-pair regression (`test_visible.py`) was run before implementation
and failed with `NotImplementedError`, then was rerun after this revision.
