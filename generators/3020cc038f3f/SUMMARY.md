# 3020cc038f3f

Read the control at `(0,0)`: `3=union`, `4=XOR`, `5=intersection`. Crop the connected color-1 and color-2 operands to their own bounding boxes, combine their normalized masks, and paint the result color 8 on the maximum operand box (`[[0]]` when empty).

Generator v4.0.0 constructs 7–9 × 9–11 scenes with separated connected 3–6-cell operands. The normalized masks may partially overlap or be identical. Four advertised axes—`grid_h`, `grid_w`, `ctrl`, and `overlap_kind`—are exact, observable, and supported in every difficulty band. A strict validator, Python cross-check, executable canonical-fitting rival, semantic witnesses, 144 task tests, and a 100+ draw-per-band Racket-backed probe are retained with the review.

Kind: `per_puzzle`. Selected version: `4.0.0`. Canonical rule hash: `d73f3f4b1c32`.
Approval is derived by the catalog from current code and retained evidence.
