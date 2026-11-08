# 260384c90f6f

Square grid size ∈ {11, 17, 23} with PERIOD-6 LATTICE: ROW 5, 11, 17 and COL 0, 6, 12, 18 (those that fit) are filled with LINE_COLOR. The grid splits into 3×3 INTERIOR CELLS at (6r+1..6r+3, 6c+1..6c+3) for each block (r, c). The TEMPLATE is a 3×3 binary mask drawn from 7 KINDS (sparse/dense/diagonal/centered/corners/L_shape/cross) with 3-5 mark positions. Each interior cell has a SUBSET of the template marks (with at least one block missing ≥1 template position) in MARK_COLOR. Rule (FILL MISSING TEMPLATE POSITIONS WITH LINE_COLOR): INFER the TEMPLATE = UNION of mark positions across ALL interior cells. For EACH interior cell and EACH template position not currently marked: PAINT that cell with LINE_COLOR. Existing marks and separators stay. Net: each cell completes the full template; missing positions fill with the line color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
