# 7c7f1f574a18

Classify each same-colour foreground component against the unique modal background by the topology of gaps inside its bounding box. A solid bounding box, or any gap region that does **not** reach the bounding-box boundary, is closed: preserve the object's rows and shape, recolour it 2, and dock it left. If every gap reaches the bounding-box boundary, the object is open: recolour it 3 and dock it right.

Version `3.0.0` pins canonical `RULE_HASH = e048ab46f343`. Ordinary scenes contain an irregular hole-bearing closed object, a solid closed object, and an open almost-ring; source positions cross destination roles so starting-side shortcuts fail. Canonical-scale/profile anchors are mixed with binary and multicolour variants. Exact controls are `grid_h`, `grid_w`, `n_closed`, `n_open`, and `palette_profile`.

Kind: `per_puzzle`. Final generator SHA-256: `27d4ef0b4f69c061c19b98ecb426edae19013204771b4b34c4a6e47ad9c5902f`.
