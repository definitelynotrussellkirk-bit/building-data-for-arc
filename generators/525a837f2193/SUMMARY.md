# 525a837f2193

Grid laid out as a CELL LATTICE: rows × cols (~4-6 each) DATA BLOCKS, each block a cell_size×cell_size square (cell_size=2), with 1-cell SEPARATOR rows and SEPARATOR columns of 0 between adjacent blocks. Every data block is filled with the BACKGROUND COLOR 1 EXCEPT EXACTLY ONE ANOMALOUS BLOCK, filled with some other non-{0, 1} color. Total grid dims: h = rows*2 + rows-1, w = cols*2 + cols-1. Rule: locate the anomalous block's row-of-blocks and col-of-blocks. REPAINT EVERY data block in that ROW-OF-BLOCKS to the anomaly color, and EVERY data block in that COL-OF-BLOCKS to the anomaly color, leaving separators 0 untouched. Net: the anomalous color spreads to fill the entire row and column of blocks containing it — a 'plus shape' painted across the lattice.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
