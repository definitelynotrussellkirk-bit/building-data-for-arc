# b9ba0104b1b6

0-bg grid (h, w~5-25) containing a SINGLE FOREGROUND SHAPE in some non-zero fg_color, with shape_kind ∈ (rect / L_shape / hollow_ring / random_blob / line_h / line_v / cross / scatter / diagonal) filling a smaller bbox (shape_h × shape_w, 2-12 each) inside the canvas, padded by ≥1-3 bg cells on each side. The shape's bbox is strictly smaller than the grid in at least one dimension. Rule: APPLY CROP-TO-CONTENT — compute the BOUNDING BOX of all non-bg cells (rmin..rmax × cmin..cmax). CROP the grid to exactly that bbox — output is the rectangular subgrid containing only the content, with all bg padding outside the bbox stripped away. Net: input is padded shape; output is the tight bbox crop of the foreground.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
