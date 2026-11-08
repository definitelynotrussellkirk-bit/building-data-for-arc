# 843016da288b

0-bg grid (h~8-11, w~8-11) with 2-3 SMALL COLOR-2 BLOBS — each a 3-5 cell 4-connected blob grown by random adjacency walk (grow_blob helper). Each blob is painted entirely in COLOR 2. Blobs are placed at non-overlapping non-touching positions (track used cells across attempts). Each blob is constrained NON-RECTANGULAR — its cell count is strictly less than its bbox area (so the bbox has at least one bg-0 cell), guaranteeing the rule's output differs from the input. Rule (REPLACE EACH 2-BLOB WITH ITS BBOX OUTLINE IN COLOR 2): for EACH 4-CONNECTED color-2 component in the input: COMPUTE its bbox (r1, c1, r2, c2). ERASE the original blob cells (set to bg-0). PAINT the BBOX OUTLINE (top row r1, bottom row r2, left col c1, right col c2 of the bbox rectangle, all 4 edges) with COLOR 2. The BBOX INTERIOR (strictly inside) stays bg-0. Other cells outside any blob's bbox stay bg-0. Net: each irregular 2-blob is replaced by a hollow color-2 rectangle outline tightly bounding where the blob was.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
