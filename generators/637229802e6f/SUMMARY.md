# 637229802e6f

A canonical 4×4 grid has magenta (6) background, exactly one red (2) marker, and one of four source-observed decoration profiles: 3 cells/3 colors, 4/4, 7/4, or 7/6. The red marker selects its 2×2 quadrant. The output fills that quadrant with red and every other cell with magenta; all decorations are discarded.

Version `4.0.0` exposes only three exact, pixel-observable controls: `marker_quadrant`, local `marker_slot`, and `decoration_profile`. Its finite output codomain is the four quadrant masks. The default four-step schedule visits every quadrant once, while marker slot and decoration profile remain constant inside an aligned answer block so nuisance features do not identify the answer branch.

The generator includes strict source-bound validation, an independent Python rule mirror, executable rivals/witnesses, a three-demonstration identifiability contract, 127 focused tests, and `workspace/probe_contract.py` for exhaustive finite-contract replay. Canonical Racket semantics were not changed; the selected task-local authority copy was synchronized byte-for-byte to the existing canonical program while archival `raw_code` remained unchanged.

Kind: `per_puzzle`. Selected version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
