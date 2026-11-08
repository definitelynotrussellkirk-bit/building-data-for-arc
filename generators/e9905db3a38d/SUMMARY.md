# e9905db3a38d

Two square templates, colored 1 and 2, appear above a two-row code grid. Codes
1/2 paste the corresponding template and codes 3/4 paste its clockwise
rotation. Decoded tiles are separated by one background row and column.

The reviewed `4.0.0` generator uses a four-profile curriculum
(`canonical`, `compact`, `wide`, `large`) in every difficulty band. One quarter
of default samples are canonical-linked 3×3-template/three-code-column scenes;
the remaining profiles vary tile size and active mosaic width. Every ordinary
sample exposes all four code branches, uses two distinct rotation-asymmetric
templates, randomizes code locations, and keeps both input dimensions strictly
larger than the decoded output.

Only two honest override axes remain: `tile_size=2..4` and
`n_codecols=2..4`. The selected Racket rule was not changed; its normalized hash
is pinned as `7b04fc79d5f0`.

Kind: `per_puzzle`. Reviewed version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
