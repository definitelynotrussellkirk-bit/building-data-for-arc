# dc9884cdb6ae

8-bg grid with a connected zero field and one connected 2-region. The 0s are distributed unevenly: at least one ROW has the maximum 0-count (≥ all other rows), and at least one COL also has the maximum 0-count. Rule: count 0s per row → max-rz. Count 0s per col → max-cz. For each 0-cell at (r, c), if row r has count max-rz OR col c has count max-cz, replace it with color 3. Otherwise leave it as 0. Other cells (8, 2) are preserved. The generator keeps 8/2 as low-component regions like the canonical examples instead of scattering 2s as independent speckles.

Kind: `per_puzzle`. Imported version: `2.4.0`.
Approval is derived by the catalog from current code and retained evidence.
