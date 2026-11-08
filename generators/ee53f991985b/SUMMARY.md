# ee53f991985b

A 0-background grid contains at least one complete same-color rectangular outline and at least one connected incomplete rectangular frame. For each 4-connected nonzero component, fill its entire bounding box only when the component is exactly the border of that box; leave incomplete frames and other non-outline components unchanged.

Production v3.0.0 always includes the broken-frame contrast that refutes the canonical-fitting shortcut “fill every component bbox.” Component bboxes are disjoint. Public exact controls are `grid_h` (7–24) and `grid_w` (10–28). The canonical rule hash is pinned in `generator.py`; detailed limits and measurements are in `notes.md`.

Kind: `per_puzzle`. Current version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
