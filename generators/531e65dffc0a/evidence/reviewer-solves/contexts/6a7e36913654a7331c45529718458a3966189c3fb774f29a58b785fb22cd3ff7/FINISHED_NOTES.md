# Blind solve notes — 531e65dffc0a

I used only the visible examples in `solve-blind/challenge.json` / README.

## Hypothesis

The multi-cell nonzero object is a binary template.  Singleton colors 2, 3, 4,
and 5 are orientation markers.  Replace the input with copies of the template:

- 2: original orientation
- 3: 90 degrees clockwise
- 4: 180 degrees
- 5: 270 degrees clockwise

Each singleton marker gives the top-left coordinate of the rotated template's
bounding box.  Filled template cells are painted with the template color; any
part beyond the grid is clipped.  The original template and marker cells are
otherwise erased.

## Evidence / probes

- Example 1: the 3x2 template copied unchanged at color 2 and becomes the exact
  2x3 clockwise rotation at color 3.
- Example 2 separates all four rotations.  In particular, the color-4 stamp at
  (6,7) is the 180-degree rotation even though its top-left mask cell is empty;
  this confirms the marker anchors the bounding box, not a filled template cell.
- Example 0 confirms clipping: the color-2 marker at the right edge retains only
  the in-bounds first template cell; the color-5 stamp is clipped at the bottom.

Implementation identifies the only repeated nonzero color as the template,
extracts its tight binary bounding box, rotates that mask, and clips each stamp.
