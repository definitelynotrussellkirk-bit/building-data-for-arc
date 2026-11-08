# cf0dd146ab42

0-bg grid (h~7-9, w~8-10) with: (a) ROW 0 holds K NON-ZERO MARKER cells (K=1..3) at random distinct columns in COLOR-2 (red); (b) BELOW ROW 1 (in rows ≥2) ONE NON-RECTANGULAR BLOB of 3-5 cells in a random color from {3..8}. The blob is non-rectangular (bbox area > cell count) so rotation changes its shape. Output uniq_out=35 (intrinsic — K mod 4 × few blobs × colors normalizes). Rule (ROTATE BLOB BY K MOD 4): COUNT K = number of non-zero cells in row 0. COMPUTE rotation = K mod 4 (0=identity, 1=90°CW, 2=180°, 3=270°CW). CROP the BLOB to its BBOX. APPLY the rotation. EMIT the rotated crop as output. Net: row-0 count drives the blob's rotation.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
