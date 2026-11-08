# 13d2544b2b64

Two all-zero rows and two all-zero columns partition an 8×8 input into a 3×3 array of 2×2 panels. At every local panel coordinate:

- an equal non-background color in the left and right panels paints the corresponding middle-column cell;
- an equal non-background color in the top and bottom panels paints the corresponding middle-row cell;
- when both marks disagree at the center panel, the horizontal mark wins.

Generator version `3.0.0` uses one exact observable axis, `scene_profile`, and cycles four profiles in every four-example window:

1. `canonical_controls` — both positive orientations, an outer-middle fill, and one-sided negatives;
2. `equality_mismatch` — opposite non-background colors that differ and therefore do not fill;
3. `horizontal_precedence` — a horizontal/vertical crossing with different colors;
4. `target_overwrite` — a valid match replaces an existing non-background target.

Every generated input has the canonical `(height, width, palette-size) = (8, 8, 4)` signature. The selected Racket authority is pinned by `RULE_HASH = "301b331591ad"`.

Kind: `per_puzzle`. Approval is derived by the catalog from current code and retained evidence.
