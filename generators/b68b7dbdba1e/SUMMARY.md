# b68b7dbdba1e

0-bg grid (h=4, w=7-8, canonical-sized). The BOTTOM ROW carries TOKEN cells of colors {1,2,3,4} at scattered columns (each token = a transform KEY: 1=rotate-cw, 2=rotate-180, 3=flip-lr, 4=transpose). Above the bottom row (the FIELD, last column excluded) sit N_MOTIFS = 2 small 4-connected blobs in DISTINCT colors drawn from {5,6,7,8,9} (NOT the token colors), each grown by random adjacency walk and placed with an 8-conn 1-cell buffer. Tokens are placed so each motif's nearest token varies (keys differ across motifs). Rule: extract every 4-connected field component, crop to bbox, TRANSFORM by the key of the NEAREST bottom token (by horizontal center), then PACK the transformed crops left-to-right into a small center-aligned gallery with 1-cell gaps.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
