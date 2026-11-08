# ad52210ad00d

0-bg grid (h×w, ~5-12 by ~5-14) with 2-4 color-2 SEED cells in scattered positions (≥2-cell separation so diagonal decorations from one seed don't collide with another). Seeds preferably in interior so all 4 diagonal neighbors exist. Rule: build fresh 0-canvas. For each cell (r, c), check its 4 diagonal positions for a color-2 seed: if (r+1, c+1)=2 paint cell 3; if (r+1, c-1)=2 paint 6; if (r-1, c+1)=2 paint 8; if (r-1, c-1)=2 paint 7. (Priority TR/TL/BR/BL.) Each 2-seed at (sr, sc) produces a diamond of colors around it: (sr-1, sc-1)=3, (sr-1, sc+1)=6, (sr+1, sc-1)=8, (sr+1, sc+1)=7.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
