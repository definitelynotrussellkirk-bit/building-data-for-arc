# 40e85135fbf8

Read row headers from column 0 and column headers from row 0, discard the header row/column, and build their colored equality matrix: output[r][c] is the shared nonzero header color when the two headers are equal, else 0.

Kind: `per_puzzle`. Selected version: `4.0.0` (imported baseline: `3.0.0`).
Approval is derived by the catalog from current code and retained evidence.

Use six ordered demonstrations. The sampler varies private header colors across
all three numeric ranks and provides a nonmaximum row gap and column gap in
every six consecutive draws. Low/high palette controls retain their exact sets;
`mixed` adds the other 82 three-color subsets of colors 1–9.
Arbitrary query holdouts are not supported by this teaching guarantee.
