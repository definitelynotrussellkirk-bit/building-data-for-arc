# 73906110dd67

Version `4.1.0` generates an 8..18 by 10..18 zero-background grid with three or four diagonally separated monochrome objects. Object colors and occupied cell areas are distinct. The authoritative rule extracts each 4-connected nonzero object, crops it tightly, sorts crops by occupied cell count from largest to smallest, and stacks them top-to-bottom with one blank row between crops. Crops are left-aligned and the output width equals the widest crop.

The sampler uses staggered, moat-separated left/right layouts rather than a fixed corner lattice; exact scan order is preserved while row and column origins vary across the full canvas. The palette supports every foreground color 1..9, and scheduled canonical profiles cycle through all canonical canvas sizes: 8x11, 9x10, and 10x10.

Four scheduled profiles provide redundant teaching evidence. Two canonical three-object/width-two profiles refute fixed-width output, while two generalized four-object/bounding-box-conflict profiles refute “keep only three objects” and bounding-box-area sorting. Therefore every four demonstrations in a five-pair consecutive lesson identify all declared rivals even when any pair is held out as the query.

Declared exact controls are `grid_h` (`8..18`), `grid_w` (`10..18`), `n_blobs` (`3..4`), `size_pattern` (`consecutive|spread`), `input_size_order` (`ascending|descending|zigzag`), `palette_kind` (`low|high|mixed`), and `max_bbox_width` (`2..3`).

Kind: `per_puzzle`. Reviewed version: `4.1.0`. Canonical rule hash: `9b7f117d5438`.
Approval remains a catalog/maintainer decision; passing review checks does not itself admit training data.
