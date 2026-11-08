# 5ffd8d801705

Distinct-color solid 2x2 squares are placed at arbitrary non-overlapping anchors on a 4..14 grid. Default scenes deliberately mix edge/interior positions, modulo-3 anchor classes, and checkerboard parities. The selected rule replaces every square by its main diagonal—keeping top-left and bottom-right—and preserves nonzero cells outside any square.

Kind: `per_puzzle`. Current version: `2.1.0`. Canonical rule hash: `c845504525a2`.

The generator realizes `n_blocks` exactly or rejects an impossible packing loudly. Its validator requires every nonzero color to be exactly one solid 2x2 square. Named coordinate-mask rivals and a lesson-level identifiability gate protect against recurrence of the former stride-3 shortcut.
