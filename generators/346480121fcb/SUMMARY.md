# 346480121fcb

A zero-background grid has a header row with a selector at the upper-left and a
transform key at the upper-right. The selector is one of colors 2–7; the key is
1–5 for identity, clockwise rotation, left/right reflection, transpose, or
180-degree rotation. The body contains 2–4 separated monochromatic objects in
distinct colors, exactly one of which matches the selector color. Crop that
object to its bounding box, apply the keyed transform, and crop to content.

The canonical generator supports exact public overrides for heights 6–14,
widths 9–16, all five transform keys, and 2–4 objects. Every advertised override
is recoverable from the returned grid through `observe_overrides`, malformed or
unknown controls fail loudly, and ordinary easy lessons no longer collapse to
identity-only transforms.

Kind: `per_puzzle`. Current reviewed version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
