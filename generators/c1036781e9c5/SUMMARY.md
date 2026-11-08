# c1036781e9c5

0-bg grid (h, w~10-16) with: (a) 1-2 RECTANGULAR FRAMES (perimeter outlines) of size 5×6 to 8×9, in some FRAME_COLOR (the most frequent non-zero color), placed by bias (right_lean / centered / corner / scattered). At least one frame is LARGER than the other (the largest is the target); (b) 3-5 SCATTERED DOT CELLS in a SECOND non-frame color (DOT_COLOR) outside the largest frame, plus 1-2 dots INSIDE the largest frame's interior. Rule: identify the MOST FREQUENT COLOR (FRAME_COLOR) — its cells form the rectangular frames. PICK the LARGEST FRAME component (by bbox area). CROP the grid to that frame's bbox. REPLACE the frame's perimeter cells with the DOT_COLOR. Net: output is the largest frame cropped, with its perimeter recolored to the dot color and its interior dots preserved.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
