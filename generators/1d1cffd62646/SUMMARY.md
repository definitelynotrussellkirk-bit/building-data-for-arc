# 1d1cffd62646

Three equally spaced, collinear dots define a center and ring spacing. The
unchanged canonical Racket rule draws concentric square outlines in the dot
color, including the center and outlines clipped at the grid edges.

Kind: `per_puzzle`. Generator version: `1.2.0`.

The deterministic sampler supports vertical, horizontal, and both diagonal
directions, dimensions `10..30`, Chebyshev spacing `2..6` where all three dots
fit, and a single dot color `1..9`. The supported override names are `grid_h`,
`grid_w`, `step`, `dot_color`, and `orientation`. Numeric overrides must be
exact integers; `None` leaves a control unpinned. Unsupported legacy controls
and impossible combinations raise errors rather than silently changing the
request. Difficulty affects default dimensions only; explicit dimensions may
use the full valid range.

`self_check` enforces rectangular integer grids and the three-dot geometry.
Metadata cannot bypass these checks. Focused regressions are in
`tests/test_generator_repair.py`.

Approval is derived by the catalog from current code and retained evidence.
