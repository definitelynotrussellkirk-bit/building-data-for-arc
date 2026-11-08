# 9e10061f96e5 — transform-equivalence matrix

A zero-background input contains 2–4 horizontal monochrome shape panels,
separated by exactly one full-height zero column. Crop and binarize each panel,
canonicalize its occupied cells under the full eight-element dihedral group
(four rotations and four reflected rotations), and emit an N×N relation matrix:
5 on the diagonal, 2 for D4-equivalent off-diagonal pairs, and 0 otherwise.

The version 3.0.0 sampler covers all eight D4 classes in the canonical inputs
plus compact additional classes with 3–8 occupied cells. Its five-sample lesson
cycle explicitly refutes identity-only, rotation-only, and equal-cell-count
shortcuts. `n_panels` is the only exact public override; every value 2, 3, and 4
is honored in every difficulty band. Difficulty only skews the default panel
count distribution. The finite output alphabet contains all 22 equivalence
matrices possible for N∈{2,3,4}.

Selected canonical authority hash: `788540441b76`. The active Racket transform
list contains all eight unique D4 operations; archival raw source is retained
unchanged for provenance.

Kind: `per_puzzle`. Imported/reviewed version: `3.0.0`.
Approval remains a catalog decision derived from current code and retained evidence.
