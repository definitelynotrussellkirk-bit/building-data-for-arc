# d30c6cb51dac

Split the 5-row input into 5-column panels separated by one zero column, crop each panel to its nonzero bounding box, and binarize nonzero cells. Return an N×N matrix with 8 on the diagonal and 2 off diagonal exactly when the destination panel is the left/right or up/down reflection of the source panel; all other off-diagonal cells are 0. Ordinary draws contain a real reflection pair plus a 90-degree rotation decoy, and larger draws also contain an exact-copy decoy whose off-diagonal relation remains 0 for asymmetric motifs.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
