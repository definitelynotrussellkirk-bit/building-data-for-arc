# 800735f51c58

0-bg grid (h, w~12-22) with 3-6 4-CONNECTED OBJECTS in distinct non-bg colors, mixing SOLID BLOBS (no enclosed holes, 3-6 cells) and HOLLOW FRAMES (rectangular outlines with 1-2 interior 0-holes inside their bbox). Each object's bbox dimensions vary. Objects are 4-conn isolated. Rule: identify all objects and their (HOLE COUNT, CELL COUNT). SORT objects by (hole_count ASC, cell_count DESC) — fewest-holes first, ties broken by largest size first. For each sorted object, CROP to its bbox. VERTICALLY STACK the cropped shapes, each HORIZONTALLY CENTERED in a strip of width = max bbox width, with 1-cell 0-gaps between successive shapes. Output: a tall centered stack of shapes ordered by (holes asc, size desc). Net: input scene is packed vertically by hole-then-size ranking.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
