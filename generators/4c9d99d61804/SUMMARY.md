# 4c9d99d61804

A 0-background grid contains exactly one red(2) start, one green(3) goal, gray(5) walls, and one pair of equal-colored portals chosen from 7/8/9. Run four-neighbor BFS in up, down, left, right order. Entering a portal teleports to its twin before the state is queued. Paint only the intermediate 0-cells of the selected shortest route yellow(4), preserving start, goal, walls, and portals. A five-profile schedule proves that a portal can be either useful or irrelevant and disambiguates all three adjacent priority comparisons in the canonical BFS order.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
