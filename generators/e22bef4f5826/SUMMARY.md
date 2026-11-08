# e22bef4f5826

0-bg grid (h ∈ 6-8, w ∈ 7-9) with: 2-3 NON-OVERLAPPING BLOBS, each a 2-3 cell irregular blob built via grow_blob random walk, each in a DISTINCT color drawn from {1..9}. Blobs placed with shared used-set tracking. Each blob's bbox checker-fill differs from the input (since blobs are non-rectangular or small). Rule (FOR EACH NON-BG COMPONENT, FILL ITS BBOX WITH A CHECKER PATTERN IN THE COMPONENT'S COLOR — CELLS WHERE (R - R1 + C - C1) % 2 == 0 GET THE COLOR, OTHERS STAY 0): For EACH blob with color c and bbox (r1..r2, c1..c2): For EVERY (r, c) in the bbox: IF (r - r1 + c - c1) % 2 == 0: PAINT g[r][c] = color; ELSE: PAINT 0 (overwriting the blob's interior). Net: each irregular blob expands to a checker-filled rectangle in its color.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
