# generic_extraction_gen3

gen3: remove a pervasive noise color, recolor-map two colors, crop-to-content.

Transform:
  `(crop-to-content (recolor-map (remove-color g NOISE) (hash A B C D)))`
A large grid is flooded with a pervasive NOISE color (scattered far beyond
the meaningful shape's bounding box). remove-color erases NOISE to bg, a
recolor-map swaps the shape's two structural colors (A->B, C->D), and
crop-to-content extracts the tight bounding box of the surviving shape.
Output is the small, recolored shape pulled out of the noisy field.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
