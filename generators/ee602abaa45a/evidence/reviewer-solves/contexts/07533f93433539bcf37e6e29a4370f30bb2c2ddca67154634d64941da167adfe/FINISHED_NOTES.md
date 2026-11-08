# Solve work log

This is a human work log based only on `solve/challenge.json` after preparation. I had earlier rule exposure while repairing the generator, so this is explicitly not blind; I did not consult the Racket source, generator source, private labels, or prior solution text during this solve phase.

## Visible-example hypothesis

Each input contains two high-color rectangular frames. Inside each frame are two small candidate templates: color 1 in the left 3×3 slot and color 2 in the next 3×3 slot. The first two cells of the frame's bottom interior row are a selector (1 or 2) and an operation code.

Across the three visible pairs, code 3 preserves the selected crop, 4 rotates it 90° clockwise, 5 rotates it 180°, and 6 flips it left/right. The transformed nonzero cells are recolored to the surrounding frame color. Frames are processed in reading order by frame top row and then left column, not merely left-to-right. Their pieces are concatenated with one blank column and vertically centered; when the height difference is odd, the extra blank row is below the shorter piece (floor offset).

## Implementation

`solution.py` finds the two high-color connected frame borders, reads each frame's selector and transform code, tight-crops the selected slot, applies the inferred transform, recolors it, and packs the two pieces. The parser deliberately excludes the code row from candidate extraction.

## Attempt 1

Implemented the complete hypothesis directly. The three demonstrations already distinguish candidate selection, non-identity transforms, crossed reading order, and centering, so no deliberate negative was needed.
