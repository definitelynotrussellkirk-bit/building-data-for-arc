# 551b790d352e

Top 5 rows hold 3 library panels at column offsets {0, 6, 12} (5 cols each); each panel has a distinct non-zero shape in a distinct color. Row 6 has 3 instruction cells: g[6][0]=selector color (matches one library panel), g[6][1]=transform code (1=identity, 2=cw90, 3=180, 4=ccw90, 5=flip-lr), g[6][2]=output recolor. Rule selects the matching library panel, crops to its non-zero bbox, applies the transform, then recolors all non-zero cells to the output color.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
