# 5df4d341f399

0-bg grid (h ∈ 12-20, w ∈ 13-22, by difficulty) with: (a) N_SHAPES ∈ 2-4 MULTI-CELL SHAPES drawn from _BY_HOLES bank (keyed by hole count 0-3): 0-hole (2×2 solid, T-tet, 2×3 solid, T-pent), 1-hole (3×3 ring, 3×4 ring, 4×3 ring), 2-hole (3×5 frame with middle bar, 4×4 with two side holes), 3-hole (5×5 with cross dividers, 3×7 with three holes). Each shape painted in a DISTINCT color from a 4+ color palette drawn from {1..9}, with STRICTLY DISTINCT HOLE COUNTS (rng.sample of [0,1,2,3] keys); (b) ONE ISOLATED SINGLE-CELL MARKER (no neighbors) painted in the MARKER COLOR (palette[0]). Rule (FIND THE MARKER → ITS COLOR IS THE TARGET; FIND THE SHAPE WITH THE MOST HOLES (BBOX-INTERIOR BG CELLS); CROP IT, SCALE 2× (EACH CELL → 2×2 BLOCK), RECOLOR EVERY CELL TO THE MARKER COLOR, OUTPUT): EXTRACT every shape with its hole count. SELECT max-holes shape. CROP to bbox. UPSCALE by 2. RECOLOR to marker. OUTPUT. Net: marker dictates color, most-holed shape dictates form, output is 2x scaled.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
