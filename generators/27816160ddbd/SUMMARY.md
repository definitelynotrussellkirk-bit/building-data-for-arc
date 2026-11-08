# 27816160ddbd

0-bg grid (size varies) with: (a) ONE LARGEST COMPONENT — a RANDOM polyomino (5-14 cells) with a NON-UNIFORM row profile; (b) 1-4 SMALLER DISTRACTOR COMPONENTS (strictly fewer cells). All components in DISTINCT colors, non-touching with 1-cell padding. The largest is unique. Rule (ROW-PROFILE HISTOGRAM OF LARGEST): identify the LARGEST COMPONENT. For each ROW of its bbox, COUNT how many cells are non-bg (belong to the component) — this gives a row profile [n1, n2, ..., nh]. EMIT a HISTOGRAM as the output: each row of the output shows ni cells of the component's COLOR left-justified, padded with 0. Net: largest component's per-row cell count becomes a left-aligned color-bar histogram.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
