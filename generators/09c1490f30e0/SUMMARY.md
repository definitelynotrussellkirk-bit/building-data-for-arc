# 09c1490f30e0

BG-COLOR (bg ∈ {0, 2..4, 6..9}, excluding 1 and 5) grid (h, w ~ 4-18) with: (a) 1..n_dots COLOR-5 (gray) DOT CELLS placed via one of 8 LAYOUTS (random / cluster / row / column / diagonal / scattered / blob / corners) constrained to a POSITION BIAS region (random / top / bottom / center / spread); (b) optional DECOY CELLS in 0..3 non-{bg, 1, 5} colors scattered at low density (0..0.15). All other cells stay bg. Rule (FOR EACH GRAY-5 DOT, KEEP THE DOT AND PAINT COLOR 1 AT ALL ITS 8-NEIGHBORS): for EACH CELL (r, c) in the input: IF v=5, KEEP it as 5 in the output. ELSE: CHECK if ANY of its 8 surrounding neighbors has value 5. IF YES: PAINT (r, c) with COLOR 1. IF NO: SET (r, c) to bg-0. Net: gray dots survive; each dot grows a halo of 1s in its 8-neighborhood; all other cells (including decoys) are zeroed out.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
