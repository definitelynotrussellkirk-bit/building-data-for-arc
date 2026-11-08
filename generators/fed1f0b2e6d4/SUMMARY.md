# fed1f0b2e6d4

0-bg grid with 2-6 BLOBS, each a random 4-connected shape in a DISTINCT COLOR from {1..9} and a STRICTLY DISTINCT SIZE (so the area-sort is unambiguous). Blobs are placed at NON-TOUCHING positions (1-cell orthogonal gap). Rule (CROP EACH BLOB TO ITS BBOX, VSTACK SORTED BY AREA, ASCENDING): find all 4-CONNECTED non-0 COMPONENTS (color-blind connectivity). Compute each component's BBOX CROP and AREA (cell count). SORT crops by area ascending, tiebreaking by bbox top-row then left-col. VERTICALLY STACK the bbox crops top-to-bottom in that order, left-aligned, with a 1-row gap between them; width = max crop width (0-padded). Net: blobs are gathered into a vertical gallery sorted small-to-large.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
