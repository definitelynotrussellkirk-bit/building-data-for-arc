# 1a5d49e539de

A 20--23 square grid contains four separated, same-colour 8-connected objects.
Exactly three object shapes are left-right symmetric and exactly one is not; the
output is the tight bounding-box crop of the unique asymmetric object.

The reviewed generator uses a three-example target-size schedule and a
four-example position schedule to refute fixed size, scan-order, horizontal
position, and unique-colour shortcuts. Its only public controls are exact
`grid_size` and `color` axes.

Kind: `per_puzzle`. Reviewed version: `3.0.1`. Rule hash: `71d6cfb99295`.
Approval is derived by the catalog from current code and retained evidence.
