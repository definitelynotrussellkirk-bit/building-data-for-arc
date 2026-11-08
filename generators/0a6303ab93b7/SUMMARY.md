# 0a6303ab93b7

Top-left selector color + top-right transform code crop the first matching object (rot-cw / rot-180 / flip-lr / identity). multi_candidate boards carry TWO selector-colored objects (top-left bbox order wins); weird_code boards use codes 5-9 (identity); corner_wins boards deliberately set code == sel so the 1-cell code object wins and the output is [[sel]]; symmetric boards make the transform invisible on a symmetric shape. Frames/blobs in other colors are decoys (the rule has no frame logic).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
