# a3e8838f9a38

Square n × n grid (n in 3..5) with a binary mask using bg=0 and one fg color (the mode). Rule: output is n² × n². For each (R, C) where R, C in [0, n²-1]: br = R//n, bc = C//n (outer block index); sr = R%n, sc = C%n (inner cell index). If input[br][bc] is fg (non-zero), then output[R][C] = fg if input[sr][sc] is bg, else 0. If input[br][bc] is bg, output[R][C] = 0. Equivalent to tiling the inverse of the input onto the fg anchor positions — a fractal.

Kind: `per_puzzle`. Imported version: `1.2.1`.
Approval is derived by the catalog from current code and retained evidence.
