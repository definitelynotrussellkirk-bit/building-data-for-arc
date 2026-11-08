# 8bc82608e55f

0-bg grid (h ∈ 9-11, w ∈ 11-13) with: (a) ONE HOLLOW RECTANGULAR FRAME of size fh × fw (fh, fw ∈ 3-4) drawn at a random non-overlapping interior position in palette[0] color; (b) 1-2 SOLID 2×2 BLOBS in palette[1:] colors (distinct from frame color), placed at random non-touching positions (no 4-adjacency with other blobs or the frame). Palette drawn from {1..9}\{0}. Rule (KEEP BLOBS WHOSE BBOX INTERIOR HAS AT LEAST ONE 0-CELL FULLY ENCLOSED BY THE BLOB (HOLEY OBJECTS); DROP BLOBS WITH NO HOLES (SOLID OBJECTS)): EXTRACT every 4-connected non-bg COMPONENT. For EACH: COMPUTE its bbox; CHECK if any 0-cell inside the bbox is fully enclosed by the component's cells. IF YES (holey): KEEP. IF NO (solid): ERASE every cell of the blob to 0. Net: hollow frames survive; solid blobs vanish.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
