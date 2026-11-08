# 531905d00c4b — Decode the Index Grid into a Prototype Mosaic

A zero-background input has a top prototype library, its first completely zero row as a separator, and a lower color-index matrix. The library contains 3–5 distinct-color four-connected objects arranged left-to-right with blank columns between their bounding boxes. Crop every prototype independently, then top-left pad all crops to the largest prototype height and width. Crop blank top/left padding around the lower nonzero index rectangle. Replace each index token with the matching padded prototype, with no gaps between tiles.

The sampler uses four deterministic teaching profiles in a repeating schedule:

1. `canonical_core` — exact canonical-size/palette support (`6×11` or `7×11`, three prototypes);
2. `shifted_prototype` — prototypes with different vertical offsets, defeating absolute-library-row padding;
3. `padded_index` — blank rows/columns before the lower matrix, defeating failure to crop the index;
4. `broad_tiles` — non-`3×3` common tile sizes, defeating fixed-size substitution.

All advertised exact overrides are valid in every difficulty band and are recoverable from pixels by `observe_overrides`. The canonical Racket authority is unchanged and pinned by `RULE_HASH = 2ace815dad55`.

Kind: `per_puzzle`. Selected generator version: `4.0.0`.
