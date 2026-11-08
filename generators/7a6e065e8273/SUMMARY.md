# 7a6e065e8273 — Halo Without the Center

A 6–12 by 6–12 zero-background grid contains 1–6 nonzero interior seed cells. Seeds are never orthogonally adjacent, may repeat colors, and may be color 5 or another non-cyan ARC color. The output is a fresh zero grid with cyan (`8`) painted at the four cardinal neighbors of every seed; original centers are omitted and overlapping halos are unioned. Source color is a distractor: every halo is cyan.

The public exact axes are `grid_h`, `grid_w`, `seed_count`, and `color_profile` (`canonical`, `monochrome`, or `mixed`). Canonical sizes 8 and 9 are weighted but every declared dimension 6–12 remains directly overrideable. Default even sample indexes are non-canonical in color so every four-consecutive-pair lesson keeps at least one non-5 demonstration after any cyclic query rotation; explicit profile overrides remain unrestricted.

Kind: `per_puzzle`. Reviewed version: `3.1.0`. Canonical rule hash: `1724b71ea895`.
Approval is derived by the catalog from current code and retained evidence.
