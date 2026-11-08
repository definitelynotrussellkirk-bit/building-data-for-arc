# 39c4e8d5275c

0-bg grid (h~8-10, w~13-16) with 3 HORIZONTAL WIRES at non-touching rows (sampled from {1, 3, 5, 7}). Each wire is: ONE COLOR-2 (red) START cell at (r, c0) followed by a sequence of COLOR-1 (blue) cells at (r, c0+1..c0+length). WIRE LENGTHS are {3, 5, 7} shuffled (strictly distinct, longest is unique). Rule (LONGEST-WIRE RECOLOR): trace EACH WIRE from its RED START. COUNT the length of each wire's BLUE PATH. RECOLOR the entire BLUE PATH of the LONGEST wire to COLOR 3 (green). Other wires' blue cells stay blue. Red start cells stay. Net: longest blue wire becomes green; shorter wires keep their blue color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
