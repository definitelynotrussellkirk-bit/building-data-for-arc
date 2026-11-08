# 4887320f66db

Small (n_rows+1) × (n_cols+1) key grid (normal n_rows/n_cols vary from 2 to 6; easy keeps 2-3). Row 0 (cols 1..N) holds N COL-KEYS — values in {2, 3, 4} encoding motif ids. Col 0 (rows 1..M) holds M ROW-KEYS — values in {1, 2, 3, 4} encoding transform codes. The (0, 0) cell and the interior cells are 0. Rule: output is 3M × 3N. For each (i, j) tile (i = row-key index, j = col-key index), fetch the 3×3 MOTIF identified by col-key value, apply transform indicated by row-key value (e.g., 1=identity, 2=rot-CW, 3=rot-180, 4=rot-CCW), and place it in tile slot (i, j). Net: a 3M × 3N tile-mosaic of transformed motifs.

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
