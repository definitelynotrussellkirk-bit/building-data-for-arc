# 59a9a5c505fb

0-bg grid with N (2-4) connected non-bg components, each in its own distinct color, with OVERLAPPING bounding boxes (typically nested rectangle frames). Rule: extract every 4-conn component (objects g 0); for each output cell (r, c), set output[r][c] = the count of objects whose bbox (r1,c1,r2,c2) contains (r,c) (i.e., r1≤r≤r2 AND c1≤c≤c2). Output is a count map; the original colors are DROPPED — values are integers 0..N.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
