# dfba64721de6

FIXED 15×15 grid with COLOR-7 (orange) BACKGROUND. (a) ONE ASYMMETRIC RED(2) SHAPE drawn from a shape bank of 4-cell tetrominoes (L, J, T, S, Z, etc.); (b) ONE 2×2 GRAY(5) BLOCK. The two are separated along ONE DOMINANT AXIS (horizontal: red and gray on same rows, different columns; vertical: same columns, different rows) with the SLIDE DIRECTION from red toward gray being one of {right, left, down, up}. Rule (SLIDE RED TOWARD GRAY, DOCK; REPLACE GRAY WITH REFLECTED RED): DETECT slide axis (red position vs gray position). SLIDE the red shape as a rigid group toward gray until they are adjacent (red's leading cell touches gray's bbox). REPLACE the gray block with a REFLECTED COPY of the red shape (LR reflection if sliding horizontally, UD reflection if vertically) painted in red. Bg-7 preserved. Net: red shape docks beside gray, gray transforms into the red's mirror image.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
