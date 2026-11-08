# 091033f57174 — Commanded L-Links

Version `3.0.0`. A command cell at `(0,0)` is color 1 or 2. Every other color occurring exactly twice supplies two endpoints on distinct rows and columns. Command 1 draws horizontally from the first row-major endpoint and then vertically to the second; command 2 draws vertically first and then horizontally. Colors with any other count, including extra command-color cells, are unchanged.

The generator exposes exact controls for 8–12 row/column grids, 1–4 endpoint pairs, both commands, and four guard textures. Its four-slot default curriculum uses three demonstrations and one query and is constructed so every query rotation distinguishes the declared command, exact-count, command-exclusion, and all-pairs shortcuts. Canonical rule hash: `0ce03c4c47d8`.
