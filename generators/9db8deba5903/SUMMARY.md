# 9db8deba5903

Tile a square input into a 2×2 output of its four rotations:

- top-left: identity
- top-right: 90° counter-clockwise
- bottom-left: 180°
- bottom-right: 90° clockwise

Kind: `per_puzzle`. Selected generator version: `3.0.0`. Canonical rule pin: `847ceb038813`.

The curriculum is profile-driven rather than a Cartesian product of loosely coupled texture knobs. Each difficulty band cycles through four exact, observable scene profiles. Every band includes a canonical 3×3 two-color profile, a lawful half-turn-symmetric case, a full four-state rotation-orbit case, and multicolor/size variation. Four consecutive demonstrations refute both declared shortcuts: repeating the unrotated input in every quadrant and swapping the clockwise/counter-clockwise quadrants.

The selected Racket target is byte-exact with canonical. The previous executable source is retained as archival `raw_code` and remains execution-parity checked.
