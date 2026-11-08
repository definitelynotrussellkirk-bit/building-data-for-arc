# 1ae37a953518

0-bg grid (h~8-10, w~8-10) with: (a) 1-4 NON-TOUCHING COLOR-6 BLOBS placed in the upper rows (rows 0..h-3, leaving the bottom row for the marker) — each blob is a 1-2 cell 4-connected component grown via grow_blob with a used-set track to avoid touching neighbors; (b) ONE COLOR-2 MARKER at fixed BOTTOM-LEFT position (h-1, 0). The marker has enough horizontal clearance for the extension to fit within the grid (col 0..w-1). Rule (EXTEND MARKER RIGHT BY COUNT OF 6-BLOBS, PAINT COLOR 3): COUNT n = number of 4-CONNECTED color-6 COMPONENTS. find the color-2 marker at position (mr, mc). PAINT the cells (mr, mc+1), (mr, mc+2), ..., (mr, mc+n) with COLOR 3, but ONLY where the original cell is bg-0 (don't overwrite 6-cells). 6-blobs and the marker stay unchanged. Net: a horizontal color-3 bar of length n appears to the right of the 2-marker, encoding the count of 6-blobs as an extension length.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
