# 089c2bd1f753

0-bg grid (h~9-12, w~10-14) with: (a) cell (0, 0) holding a MARKER COLOR from a 3-color palette (the TARGET INDICATOR); (b) EXACTLY ONE TARGET OBJECT of 3-5 cells in the SAME COLOR as the (0, 0) marker, placed at a random interior position; (c) 1-2 DISTRACTOR OBJECTS in OTHER non-target colors (2-3 cells each, non-overlapping). Objects don't touch each other or (0, 0). Rule: READ marker color at (0, 0). FIND the ONE OBJECT (connected component) elsewhere that SHARES that color. CROP to that object's BOUNDING BOX and RETURN the cropped subgrid (preserving its color and shape). Distractors and marker discarded. Net: marker selects target by color; output is bbox crop of matching object.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
