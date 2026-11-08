# 8c73e339d80e

0-bg grid (h~8-10, w~9-11) with: (a) one BASE motif in color 3 (green), 3-4 cells, placed in the upper-left region; (b) 2-3 MARKER PAIRS in the right region: each pair = a CODE cell (color in {2, 4, 6, 9}) immediately to the LEFT of a color-1 (blue) MARKER cell. Rule: extract base = normalized cells of color 3. For each color-1 marker at (r, c), look at code = g[r][c-1]. Decode code → rotation count: 2→0, 4→1, 6→2, 9→3. Rotate base CW that many times. Stamp the rotated base at the marker position (anchor at marker's (r, c)), painted color 8 (cyan). Original base, markers, codes all replaced by 0 in output except where stamped cells overwrite.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.

Ordinary generated layouts include at least one marker whose chosen rotation
visibly changes the base, so the pair contradicts stamping the unchanged base at
every marker. Structurally valid symmetric canonical inputs remain accepted.
