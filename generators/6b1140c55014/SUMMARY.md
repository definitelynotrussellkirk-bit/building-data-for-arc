# 6b1140c55014

0-bg grid (h~10-16, w~12-18) with: (a) ONE FULL COLOR-4 (yellow) SEPARATOR COLUMN at sep_col (position bias: center/spread/edge); (b) a LEFT SHAPE of width k (3-4) × height left_h (2-4) in some color from the palette (non-4), placed in the left half; (c) a RIGHT SHAPE of same width k × height right_h (2-4) in a distinct color in the right half. Shape density 0.5-0.9 — both shapes have 4 corner cells set + extra cells scattered inside. Rule (VCONCAT CROPPED HALVES): identify the FULL 4-COL SEPARATOR. CROP the LEFT HALF (cols 0..sep_col-1) to its non-bg CONTENT BBOX. CROP the RIGHT HALF (cols sep_col+1..w-1) to its non-bg CONTENT BBOX. VCONCAT (stack vertically) the two crops (left on top, right below). Widths must match (both = k). Output height = left_h + right_h, width = k. Net: 4-separator drives a vertical stack of left then right cropped shapes.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
