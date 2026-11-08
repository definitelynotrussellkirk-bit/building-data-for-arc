# 3c01bf0d6576

Read non-zero 4-connected components in bounding-box reading order. The first two crops A and A' demonstrate one non-identity transform from {rotate 90 CW, rotate 180, transpose, flip LR, flip UD}. Infer that transform from the full coloured crops, then apply it to the full bounding-box crop of the third component B and output only that transformed crop. A disconnected satellite inside B's bbox is therefore included.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
