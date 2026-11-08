# ada76e18c19c — Row Span Paint

On a black grid, inspect each row independently. If and only if a row contains exactly two nonzero cells and both cells have the same color, fill the inclusive horizontal span between them with that color. Mismatched pairs, rows with a third nonzero cell, blank rows, and all other rows remain unchanged.

The generator now cycles the five authoritative input profiles exactly:

- `7×10`, palette size 4
- `8×9`, palette size 4
- `6×11`, palette size 4
- `9×12`, palette size 4
- `8×10`, palette size 4

Every default scene contains three qualifying rows using three distinct nonzero colors. A three-step teaching schedule adds one morphology-neutral counterexample row:

1. `mismatched_pair` — exactly two endpoints of different colors;
2. `extra_same_color` — three cells of one color;
3. `blocked_pair` — a same-color pair with a third-color cell between it.

Those rows distinguish the selected exact-count/exact-color rule from three shortcuts that fit every canonical pair. The counterexample cells are placed adjacent to existing endpoints so the generated connected-component count remains aligned with the canonical median.

Exact override axes are limited to `grid_h=6..9` and `grid_w=9..12`; both are recoverable from the returned grid. The module also provides a Python `rule_mirror`, `semantic_profile`, strict canonical recognizer, shortcut/witness declarations, lesson-identifiability check, and task-linked mutation fixtures.

Kind: `per_puzzle`. Current version: `3.0.0`. Canonical rule hash: `714e73d2362f`.
