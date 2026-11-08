# aea86d2776f1 — Commanded Template Mosaic

Version `2.0.0` generates the rule’s true fixed `5×11` input grammar: four commands at row 0 columns `1,3,7,9`, plus two connected asymmetric `3×3` templates in fixed frames. Commands `1..4` select the left template and `5..8` the right; command residue chooses identity, clockwise rotation, left-right reflection, or 180° rotation. The four transformed tiles form a `6×6` row-major mosaic.

The four-slot schedule repeats:

1. `canonical_core` — exact canonical `5×11`, seven-color profile;
2. `multicolor_left` — preserves multicolor pixels and uses an offset template box;
3. `multicolor_right` — a second color/crop counterexample with a different source balance;
4. `dense_counterexample` — all three declared rivals disagree.

Every four consecutive pair slots therefore refute the canonical-fitting `alternating_sources`, `monochrome_templates`, and `cropped_templates` rivals in the demonstrations regardless of which pair is held out as query. Six exact controls are pixel-observable in every difficulty band: left/right occupied cells, left/right color counts, left-source command balance, and distinct transform count.

Kind: `per_puzzle`. Selected version: `2.0.0`. Canonical rule pin: `5d25ec4af105`.
