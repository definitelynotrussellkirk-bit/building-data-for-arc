# 40dea3d45f2a — D4 panel equivalence

Four 4×4 panels in a fixed 9×9 grid contain nonzero masks. The unchanged canonical Racket rule outputs a 4×4 matrix: 8 exactly when the corresponding masks are identical up to translation, rotation, or reflection, ignoring colors.

Version 3.0.0 removes a perfect cell-count shortcut. A finite constructive bank supplies connected 3–8-cell shapes. Every three consecutive default draws include equal-area/equal-box inequivalent shapes, a reflection-only positive, and color decoupling. Other draws cover all 15 equivalence partitions, including all-equivalent and all-distinct. Shapes are independently transformed, translated within panels, and shuffled.

Exact controls: `n_classes=1..4`, `palette_size=1..4`, `grid_h=grid_w=9`. Unknown/decorative old axes now raise. The full teaching guarantee is for unconstrained default lessons, not overrides that remove the necessary examples. See notes and workspace for reproducible checks and limitations.

Kind: `per_puzzle`. Rule pin: `d5ddd0abae4d`. Generation provides inputs only; canonical Racket remains the label authority. Catalog approval is still derived from current code and retained evidence; passing local checks does not grant approval.
