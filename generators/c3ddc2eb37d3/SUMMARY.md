# c3ddc2eb37d3

0-bg square grid (h, w ~ 6-9) with: (a) THREE NON-0 TOP-ROW MARKERS at fixed column positions {1, w//2, w-2} in 3 distinct non-0 colors C0, C1, C2 drawn from a 4-color palette {1..9}; (b) TWO DISTRACTOR cells in COLOR C3 (the 4th palette color) — one at (h-1, 0) and one at (h//2, w-1). Distractors occupy lower rows / right edge where the rule will overwrite them. Rule (PROJECT TOP-ROW COLORS DOWN THEIR COLUMNS): for EACH non-0 cell (0, c) in the top row of color C: PAINT every cell (r, c) for r in 1..h-1 with COLOR C. Cells in columns without a top-row marker stay unchanged. Distractor cells in marker columns are OVERWRITTEN; distractors in non-marker columns stay. Net: vertical color stripes descend from each top-row marker, painting their columns downward; distractors outside marker columns remain as scattered noise.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
