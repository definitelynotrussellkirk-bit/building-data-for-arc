# b9d1d323c3ed

A zero-background 8–18 by 8–18 grid contains one nonzero color in a non-solid bounding box. The rule crops the exact nonzero bounding box and concatenates that crop with itself horizontally.

Version `3.0.0` alternates two lesson profiles: even sample indices reproduce the canonical 8×8 / 3×3 scale, while odd indices use a non-3×3 bbox. With three demonstrations plus one query, every consecutive four-pair lesson retains a non-3×3 demonstration under every query rotation, refuting the canonical fixed-3×3 shortcut.

Declared exact axes: `grid_h`, `grid_w`, `fg_color`, `bbox_size_kind`, `bbox_position_bias`, and `fg_layout`. Every legal Cartesian combination is constructive; malformed or unknown overrides fail loudly. The selected canonical rule is pinned by `RULE_HASH = "8d4993ada3e1"`.

Kind: `per_puzzle`. Imported/reviewed version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
