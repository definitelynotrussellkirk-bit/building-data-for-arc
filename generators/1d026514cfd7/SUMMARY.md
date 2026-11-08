# 1d026514cfd7

0-bg grid (h~9-11, w~11-13) with 3-4 CONNECTED MOTIFS each in a DISTINCT non-0 color from {2..9}. Each MOTIF is 3-5 cells grown by random neighbor extension. Motifs are placed at NON-OVERLAPPING NON-TOUCHING positions (≥1-cell padding). Rule (VERTICAL PACK GALLERY OF MOTIFS): identify all connected NON-BG MOTIFS. For EACH motif, extract its BBOX CROP. The OUTPUT is a VERTICAL STACK of the bbox crops — concatenated TOP-TO-BOTTOM (in canonical order: by color, position, or size). Background padding aligns widths. Net: motifs gathered into a vertical gallery, one above the other.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
