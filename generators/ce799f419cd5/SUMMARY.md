# ce799f419cd5

0-bg grid: n_panels (4-6) of 4-WIDE x h-HEIGHT (panel_h 4..5), separated by FULL-HEIGHT COLOR-9 (maroon) DIVIDER COLUMNS, each panel holding a SMALL MOTIF (1-3 cells) in a color from {2..7}. Rule (VERIFIED from the canonical Racket): crop the joint bounding box of ALL motif cells, remove the color-9 dividers (-> 0), and STAMP that motif-collage crop at each former divider-column position. It does NOT identify or emit a matching motif pair — see the docstring MISMATCH flag (the canonical rule and the generator's 'find-pair' design disagree; likely a bad conversion).

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
