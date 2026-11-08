# f41ae450c30b

Build an `N×N` visibility matrix for 3–4 separated, distinctly colored domino components on a zero background. Components are sorted by centroid column and then centroid row. The diagonal records component colors; an off-diagonal cell is `8` exactly when some cell pair shares a row or column and the entire segment between them contains only background or the two endpoint components.

Selected generator version: `3.0.0`.

Ordinary lessons deliberately contain a horizontal or vertical `A–B–C` chain in which `A` sees `B`, `B` sees `C`, and `B` blocks `A` from `C`. This executable witness distinguishes true line of sight from the canonical-fitting shortcut “aligned means visible even through another component.” Public controls are exact and observable: `scene_profile`, `n`, and `layout_axis`.

Kind: `per_puzzle`. Canonical rule hash: `8601bafc35ff`. The canonical Racket authority was not changed by review `review-4955a8d54ae6bb80`.
