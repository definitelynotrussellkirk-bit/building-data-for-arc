# Post-repair visible-only solve notes

This is an **exposed** solve: I inspected this task's generator and rule earlier while repairing it. After `solve_episode.py prepare`, I did not reopen the generator, Racket source, canonical data, private labels, or prior solution files; I used only `solve/challenge.json` and wrote the implementation fresh.

Visible pattern: nonzero cells are obstacles and remain unchanged. Zero cells are painted 1 in square regions. The largest empty-square regions are always painted, including every tied largest placement. Smaller empty squares are painted only when their whole footprint is disjoint from the union of largest squares; overlapping smaller-square fringe cells remain 0.

Implementation probe: compute, by reverse dynamic programming, the largest all-zero square side beginning at each cell. Form the union of all global-maximum squares. Then enumerate side lengths 2 through the maximum and add a square only when it is wholly disjoint from that fixed maximal union. Preserve obstacles and recolor selected zero cells to 1.
