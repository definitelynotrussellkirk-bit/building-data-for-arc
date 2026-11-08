# b765f6c9ebeb

Zero-background grids contain same-color 4-connected components of two kinds:
singletons, which the rule erases, and components of size at least two, which the
rule preserves exactly.  The first three default samples match the canonical
`(height, width, palette-size)` profiles `(5,6,6)`, `(5,5,5)`, and `(5,7,5)`.
They deliberately include (1) a singleton touching a differently colored
survivor and (2) same-color singleton cells touching only diagonally, so a model
cannot succeed by grouping all nonzero cells or by using 8-connectivity.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Rule hash: `22554e067bcc` (unchanged canonical Racket authority).
