# aa538df09d67

0-bg grid (h ∈ 6-10, w ∈ 8-12, by difficulty) with: N ∈ 2-4 CONNECTED MOTIFS, each a 3-5 cell connected motif built via _build_motif random adjacent-step walk, painted in a DISTINCT non-bg color drawn from {1..9}. Each motif's bbox is ≥2×2 (single-row or single-col motifs filtered out). Motifs placed at non-overlapping positions via _free check with 1-cell padding. Rule (FOR EACH 4-CONNECTED NON-BG COMPONENT, PAINT THE 4 EDGES OF ITS BBOX (TOP, BOTTOM, LEFT, RIGHT) WITH THE COMPONENT'S COLOR — TURNING THE BBOX INTO A HOLLOW RECTANGULAR OUTLINE; INTERIOR REMAINS PARTLY PAINTED FROM THE ORIGINAL MOTIF): For EACH component with color c and bbox (rmin, cmin, rmax, cmax): PAINT all cells (rmin, c) and (rmax, c) for c in cmin..cmax, and (r, cmin) and (r, cmax) for r in rmin..rmax with COLOR c. Interior cells keep their original (motif or bg) values. Net: each motif gets wrapped in its color's rectangular bbox outline.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
