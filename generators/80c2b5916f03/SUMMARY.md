# 80c2b5916f03

0-bg grid (h~6-12, w~8-18) with 2-6 SPARSE NON-BG NON-GRAY (non-{0, 5}) SOURCE CELLS each placed in a DISTINCT row, following one of 5 LAYOUTS (evenly_spaced / clustered / left_biased / diagonal / random) and one of 3 POSITION BIASES (left / center / spread). Each source is painted with a color drawn from a small palette of 2-4 distinct non-{0, 5} colors. Each source has ≥2 bg cells to its right (constraint: source column ≤ w - 4 to guarantee trail room). Optionally, decoy cells (0..0.05 density) in non-source non-trail palette are scattered. Rule (FOR EACH SOURCE CELL, SHOOT A COLOR/5 ALTERNATING TRAIL RIGHTWARD): for EACH non-bg non-gray SOURCE at (r, c) with color C: PAINT cells (r, c), (r, c+1), (r, c+2), ..., (r, w-1) alternating between COLOR C and COLOR 5 — i.e., (r, c) = C, (r, c+1) = 5, (r, c+2) = C, (r, c+3) = 5, etc. The trail extends until the right edge. Other rows (non-source) stay unchanged. Net: each source casts a striped color/gray trail to the right wall.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
