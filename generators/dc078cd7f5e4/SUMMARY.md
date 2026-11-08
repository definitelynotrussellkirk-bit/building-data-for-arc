# dc078cd7f5e4

0-bg grid with one to three CYAN(8) rectangular frames (hollow outlines) of size 5-9 per side. Inside each frame interior, 1-3 RED(2) cells are placed (not on border), preferably in the top-left quadrant so the rule's mirror operations are visible. Rule: for each color-2 cell at (r, c) inside the frame, compute mirror positions: horizontal mirror (r, 2*cc - c), vertical mirror (2*cr - r, c), both (2*cr - r, 2*cc - c) where (cr, cc) is frame center. Paint each mirror position with 2 (if currently 0 and within frame). Output preserves frame + original reds + adds mirrored reds.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
