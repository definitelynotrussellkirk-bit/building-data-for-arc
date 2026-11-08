# e51349aef7b1

Crop three square panels separated by full-height color-5 columns. Find the first
transform in identity, clockwise rotation, half-turn, transpose, left-right
reflection, and up-down reflection that maps binary cropped A to binary cropped
B. Apply that transform to cropped C and recolor it with B's foreground color.
The canonical Racket rule is unchanged at hash `cb2d64bc2f44`.

Generator v3.0.0 uses a four-profile curriculum. Two profiles deliberately have
multiple valid A→B transforms and teach first-match precedence; two have unique
transforms. A and B are translated independently so complete-panel matching is
not a valid shortcut. Any three demonstrations from a four-profile window refute
both declared rivals under every query rotation.

Exact controls are `panel_n` 5–6, `c_cells` 4–8, and `palette_id` 0–4. The final
source passed all 12 battery stages, 157 portable focused tests, 300 production
lessons with 1,200 query rotations, and exhaustive fixed-seed schedule/control
probes. See `notes.md` for scope and limitations.

Kind: `per_puzzle`. Repaired version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
