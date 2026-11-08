# a11e85424fd8

Fixed 3×11 grid with: (a) cols 0-2 = QUERY panel containing a 3-cell L-shape (after some dihedral transform) in q_color; (b) col 3 = full color-8 separator; (c) cols 4-6 = first CANDIDATE (the L-shape in hit_color, normalized orientation); (d) cols 7 = blank gap; (e) cols 8-10 = second CANDIDATE (a 4-cell distractor in other_color). Rule: extract the query shape and each candidate shape's binary support; for each candidate test all 8 dihedral transforms — the candidate whose support matches the query under some D4 transform is the WINNER. Output: the winner cropped to its bbox, recolored to the query's color.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
