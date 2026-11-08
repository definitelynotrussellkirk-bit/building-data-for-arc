# 2c420f77c907

Maze grid (walls=5, open=0, start=2, goal=3) with ONE start cell and ONE goal cell. Path consists of: (a) a straight corridor segment from start, (b) one or more rectangular ring bypasses that branch into 2 equal-length paths, (c) a straight corridor segment to goal. Rule: BFS from start and from goal to count shortest-path distance and path multiplicity for every open cell. A 0-cell is UNAVOIDABLE iff dist(s→x) + dist(x→g) == dist(s→g) AND paths(s→x) * paths(x→g) == total_paths(s→g). Mark all unavoidable cells 8; leave others unchanged. Output has 8s on bottleneck corridor cells, 0s on ring branches (where multiple shortest paths exist).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
