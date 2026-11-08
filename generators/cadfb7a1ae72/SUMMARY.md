# cadfb7a1ae72

Isolated same-color objects are read in top-left order. The output is an `N × N` relation matrix: `1` on the diagonal, `8` for two objects with the same exact row/column reflection-symmetry class, `4` for equal enclosed-hole **region** count when symmetry differs, and `0` otherwise.

The deterministic four-profile curriculum (`canonical3`, `canonical4`, `hole_priority`, `binary_holes`) makes every four consecutive examples expose all four output symbols and refute six shortcut families:

- symmetry-axis count instead of exact axis orientation;
- palindromic row/column projections instead of cellwise reflection;
- hollow-versus-solid instead of exact hole count;
- enclosed zero-cell area instead of connected hole-region count;
- hole equality before symmetry equality; and
- ascending color order instead of top-left spatial order.

Two reusable workspace auditors cover both atomic and composed alternatives. The composed audit crosses symmetry encoding, hole encoding, object order, and precedence: 36 hypotheses total, 30 of which fit every official pair, leaving 29 non-authority canonical-fit hypotheses that generated lessons must eliminate.

Kind: `per_puzzle`. Reviewed version: `3.1.0`. Canonical rule hash: `b8842d5039be`. The Racket authority was not changed; approval remains a catalog/intake decision.
