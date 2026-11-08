# 526c7883cafa

0-bg grid (h~8-11, w~10-13) with 2-4 ISOLATED 4-conn BLOBS (3-5 cells each) in distinct colors, with NON-RECTANGULAR shapes (so bbox-fill is non-trivial) and non-overlapping bboxes. Rule: extract every 4-conn non-bg blob. For each blob, find its BOUNDING BOX. FILL every cell in that bbox with the blob's color (solid rectangle fill). Net: each blob expands from its sparse shape to a SOLID FILLED RECTANGLE matching its bbox dimensions.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
