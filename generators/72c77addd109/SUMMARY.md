# 72c77addd109

Version `3.0.0`; canonical rule hash `a657cfe83f60`.

A zero-background grid contains exactly two complete hollow rectangular frames and two other connected monochrome objects, all in distinct nonzero colors. Rank frames by **interior area** and objects by **cell count**, pair equal ranks, and return a fresh zero grid with the frames redrawn at their original positions and each paired object's tight crop centered on its frame. Paste the object's nonzero cells after drawing the frame; the authoritative rule does not clip to the frame interior, so a crop larger than the interior may overwrite border cells.

The default curriculum includes canonical-size/palette anchors, rectangular and arbitrary connected solids, both frame and solid reading orders, both solid color orders, and explicit border-overwrite cases. Declared exact overrides are `grid_h`, `grid_w`, `solid_style`, `solid_rank_order`, `frame_rank_order`, `solid_color_order`, and `palette_kind`; unknown or invalid overrides are rejected. The semantic contract declares and refutes reading-order, color-order, frame-order, clipping, and filled-bounding-box rivals.

Kind: `per_puzzle`. Approval is derived by the catalog from current code and retained review evidence.
