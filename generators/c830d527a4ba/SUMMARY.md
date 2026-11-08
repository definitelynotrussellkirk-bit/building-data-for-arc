# c830d527a4ba

Extract the color-1 template and the separate code bbox.  Replace each code
cell with a recolored transform of the template, preserving zero code cells as
blank template-sized tiles:

- `2`: identity
- `3`: rotate 90 degrees clockwise
- `4`: rotate 180 degrees
- `5`: flip left-to-right

Tiles in each code row are floor-centered vertically with one blank column
between them.  The rendered rows are floor-centered horizontally with one blank
row between them.

The version 3.0.0 generator uses a four-profile deterministic curriculum
(`canonical_left`, `canonical_right`, `gapped_left`, `gapped_right`) so every
three-example lesson contains both source positions and at least one internal
code gap.  Templates are connected, bbox-filling, and asymmetric under all four
coded transforms.  Exact overrides are supported for canvas size, template
bbox, code bbox, and template side.

Kind: `per_puzzle`.  Generator version: `3.0.0`.  Canonical rule pin:
`0b137f4534ae`.
