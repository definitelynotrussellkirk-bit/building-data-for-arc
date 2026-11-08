# 05ede1ccd0f1

Full-height color-8 axis column; every non-{0,8} cell LEFT of it is mirror-COPIED to (r, 2*axis - c) in the same color (sources stay, out-of-bounds mirrors vanish, mirrors overwrite whatever sits at the destination). 8-cells left of the axis are NOT mirrored. (Was: mirrors always in-bounds onto an empty right side — the clip, overwrite, and 8-exclusion behaviors were never shown; 2 of 3 degenerates crashed the rule.)

Kind: `per_puzzle`. Imported version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
