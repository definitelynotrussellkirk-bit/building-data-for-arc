# e2bc70324918

Canonical rule: on an orange field, connect every pair of same-shape glyph centers with the line color, then stamp the input glyph at both endpoints of the original two-endpoint line.

Kind: `per_puzzle`. Generator version: `3.2.0`.

The reviewed generator now honors the declared orientation, glyph-count, glyph-kind and palette controls; supports the canonical X and five-row I templates plus additional controlled glyphs; rejects endpoint placements unless the complete stamp fits; and returns valid diagnostic boards for every declared degenerate texture.

The task-local parametric family preserves exact canonical `stamp_mode=copy` bytes and adds `stamp_mode=dilate4`: extract the normalized input glyph, orthogonally dilate that input-dependent intermediate by one cell, then stamp the result at the line endpoints. It supports 2–6 demonstrations, exactly four stable queries, and a substantive 30×30 query.

Status: reviewer-ready authoring evidence only. Owner source review, native qualification/acceptance, and any training admission remain pending.
