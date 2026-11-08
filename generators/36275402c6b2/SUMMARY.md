# 36275402c6b2

Find the unique largest same-colour 4-connected component and crop its bounding box. Every isolated horizontal pair outside that box is read left-to-right as (replacement, source), including pairs beside the crop. Recolour all matching source cells inside the crop, including source cells on its border; preserve the actual frame-colour cells.

Kind: `per_puzzle`. Reviewed version: `4.1.0`. Three demonstrations; alternating interior and border/side-witness profiles. See `notes.md` for the distribution contract and evidence limits.
Approval is derived by the catalog from current code and retained evidence.
