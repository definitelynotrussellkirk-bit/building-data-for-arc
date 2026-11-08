# 0ed4fa8c0b40 — Arrow-directed edge reflection

A grid contains one cyan support and one five-cell yellow horizontal arrow. Read direction from the apex's offset relative to the arrow's own three-cell bar. Reflect every cyan cell horizontally immediately beyond the cyan bounding box's indicated left or right edge, preserve holes and rows, and keep the original input unchanged.

Version `3.0.0` uses a linked four-profile curriculum: canonical left/right `6×9` anchors plus left/right off-center counterexamples that break absolute-grid-position shortcuts. Cyan supports are `2..3 × 2..3`, 8-connected, and sparse/asymmetric or dense. All declared axes are exact and observable; malformed textures are diagnostics only.

The task-local semantic contract names six rival operations, supplies executable witnesses, and checks that every four-example lesson is identifiable. Focused tests cover canonical parity, authority synchronization, overrides, structure, shortcut refutation, determinism, and diversity.

Kind: `per_puzzle`. Generator version: `3.0.0`. Canonical rule hash: `d42dbc127318`.
