# d5d9fdb01bdd

Generate a zero-background canvas (`5..11 × 6..12`) containing one sparse,
asymmetric nonzero pattern with a complete one-cell outer margin.  Content uses
one to three nonzero colors and may be connected or disconnected.  The
three-sample schedule contains one canonical-scale tall anchor and two distinct
wide/disconnected witnesses, so every complete demonstration set refutes both
“transpose only tall/square crops” and “use only the largest component.”

The authority rule is unchanged: find the tight bounding box of **all** nonzero
cells, preserve every internal zero and every component/color, crop to that box,
and transpose the crop.  The output dimensions are therefore `bbox_width ×
bbox_height`.

Public exact controls are `grid_h=5..11`, `grid_w=6..12`, and
`n_distinct_colors=1..3`; every advertised joint boundary combination is
constructive.  Canonical authority hash: `1b9c6046c883`.

Kind: `per_puzzle`. Selected version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
