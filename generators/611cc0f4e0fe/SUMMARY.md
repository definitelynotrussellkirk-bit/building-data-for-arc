# 611cc0f4e0fe

Matching-colored endpoints are joined only when their row and column offsets
have equal nonzero magnitude: an exact 45-degree diagonal. The Racket authority
is unchanged and pinned by `RULE_HASH = "51d7c63afd4f"`.

The selected generator is version `2.0.0`. Its only public control is the fully
observable `scene_profile`, with a deterministic four-example curriculum:

1. `canonical_opposite_slopes`
2. `same_slope_pairs`
3. `off_slope_decoy`
4. `three_pairs`

Those profiles preserve canonical support while refuting three shortcuts that
fit every canonical pair: generic Bresenham connection, requiring one pair of
each slope, and acting only on exactly two foreground colors. A fourth rival,
connecting only the first valid pair, is also tested.

Run `workspace/audit_curriculum.py` to force every profile in every band and to
rotate each profile through the query position. The current grammar deliberately
uses exactly two endpoints per nonzero color; it does not teach the authority's
first/last behavior for colors appearing more than twice.

Kind: `per_puzzle`. Imported baseline version: `1.1.1`; selected version: `2.0.0`.
Approval remains catalog-derived; reviewer checks do not admit training data.
