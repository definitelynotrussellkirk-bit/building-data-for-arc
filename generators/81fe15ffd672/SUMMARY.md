# 81fe15ffd672

0-bg grid with: (a) one KEY color cell at (0, 0) in some non-{0, 9} color; (b) 1-3 color-9 markers at distinct columns in row 0 (the count determines the transform code); (c) body (rows 1+) holds one connected SHAPE in the key color (3-5 cells). Rule: read key color from (0, 0). Count color-9 markers in row 0 = code. Collect key-colored cells outside row 0 as the shape. Crop to bbox and apply transform code (1=identity, 2=rot90, 3=rot180, 4=rot270, ...). Output is the transformed shape grid in the key color.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
