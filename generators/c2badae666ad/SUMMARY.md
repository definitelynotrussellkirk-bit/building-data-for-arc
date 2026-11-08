# c2badae666ad

0-bg grid (size varies). THREE shapes in colors 1, 2 and 3, placed apart. They are defined over a shared k x k frame by a random per-cell MEMBERSHIP: each cell belongs to some subset of the three shapes, every shape spans the full frame (so the rule's independent normalization keeps them aligned), and at least one cell belongs to EXACTLY 2 shapes. Rule: normalize each color's cells to its bbox and output the cells that appear in exactly 2 of the 3 normalized sets, bbox-cropped, in COLOR 8 (cyan). The grid size, the three shapes and their positions all vary freely (was 3 fixed shapes + grid padding).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
