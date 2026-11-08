# 4a4cce4436f0

0-bg square grid (size~8-15) with COLOR-5 (gray) WALLS forming a chamber lattice: 1-3 FULL HORIZONTAL wall rows and 1-3 FULL VERTICAL wall columns (with ≥2-row/col separation), splitting the grid into N CHAMBERS. Most chambers have EXACTLY ONE KEY cell in a DISTINCT non-wall color. Some chambers may be EMPTY (0 keys) or have 2 keys (ambiguous). Rule (FILL CHAMBERS WITH EXACTLY ONE KEY USING THAT KEY's COLOR): For EACH CHAMBER (4-conn non-5 region bounded by 5-walls): if it contains EXACTLY ONE non-wall non-0 KEY cell with color C, FILL all 0-cells in the chamber with C. 0-key and 2-key chambers stay. Walls and keys stay. Net: single-keyed chambers flood with their key's color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
