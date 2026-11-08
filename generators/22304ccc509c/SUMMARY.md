# 22304ccc509c

Version `3.0.0` generates 0-background grids for **order-preserving, per-column downward gravity**. For each column independently, the nonzero values are read top-to-bottom and packed flush against the bottom in that same order; columns never exchange cells.

The public exact controls are `grid_h=6..18`, `grid_w=6..18`, `columns=2..6`, and `palette_size=1..9`. All declared combinations are feasible, unknown/coercible overrides are rejected, and `observe_overrides()` recovers every axis from the returned pixels.

A deterministic five-profile schedule covers three canonical-size/palette anchors plus broad sparse and broad dense cases. Every default production draw is non-identity and contains both (1) a nonzero bottom-row payload and (2) a numerically descending multi-color stack. These witnesses rule out the retained “discard the bottom input row” shortcut and the canonical-fitting “sort values, then drop” shortcut.

The generator declares executable semantic witnesses, rivals, an independent Python rule mirror, a three-demonstration lesson contract, a strict task validator, and malformed mutation fixtures. The selected Racket authority and `RULE_HASH=c3638032481f` are unchanged.

Evidence: `checks/after/checks/22304ccc509c_after_battery_summary.json`, `checks/lesson-census.json`, `checks/shortcut-probe.json`, and `checks/shortcut-witness/report.json`.
