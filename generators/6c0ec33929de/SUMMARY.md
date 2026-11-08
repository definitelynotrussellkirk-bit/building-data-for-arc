# 6c0ec33929de

0-bg grid (h, w~13-15) with: (a) ONE SOLID COLOR-2 (red) RECTANGLE of size bh×bw (bh, bw=2-4) at position (r1, c1)..(r2, c2), placed according to bias (centered/scattered/near_corner/rng); (b) 1-8 COLOR-5 (gray) PIXELS at scattered positions outside the red block (in horizontal, vertical, or diagonal directions). Rule (GRAVITATE GRAYS TO RED BLOCK): for EACH COLOR-5 GRAY PIXEL, MOVE it in a STRAIGHT LINE toward the RED BLOCK. The pixel STOPS at the cell ONE STEP OUTSIDE the block's bbox in the direction of approach. If the gray is directly aligned with the block (same row/col), move axially; if diagonal, move diagonally; if not aligned, move axially to the nearest side. Paint the new position color-5, clear the original. The red block stays. Net: gray pixels migrate to halos the red block's perimeter.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
