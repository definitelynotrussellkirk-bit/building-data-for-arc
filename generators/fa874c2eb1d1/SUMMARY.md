# fa874c2eb1d1

Grid filled with a DOMINANT CANVAS color (the most-frequent non-zero color) on which 2-5 colored 6x6 HEX OUTLINES (a fixed 12-cell hexagon stencil) are drawn, each a distinct color != canvas. The hexes may OVERLAP: drawn back-to-front, a front hex overwrites cells of hexes behind it, so back hexes appear PARTIALLY OCCLUDED. A little NOISE (stray <4-cell fragments) may also appear. Rule: bg = the dominant canvas color; detect every other color's hex outline (fit remaining cells to the stencil; colors with <4 cells or no fit are dropped as noise); infer the occlusion z-order from which color covers each hex's missing cells (blocker dependencies); and OUTPUT the hexes restacked as COMPLETE outlines — an (n*6) x 6 grid on the canvas color, one full hex per 6-row band, ordered so blockers follow the hexes they occlude. (Was a 0-bg fixed 17x18 grid with 3 complete non-overlapping hexes.)

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
