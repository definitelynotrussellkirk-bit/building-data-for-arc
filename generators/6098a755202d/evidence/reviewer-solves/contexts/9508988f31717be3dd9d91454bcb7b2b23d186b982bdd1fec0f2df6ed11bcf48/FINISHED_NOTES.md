# Blind solve notes — 6098a755202d

- The gray `5` cells form a rectangular frame; cells outside it never change.
- Hypothesis: non-gray colored cells inside the frame are Voronoi sites under Manhattan distance.
- For each interior background cell, find all markers at minimum Manhattan distance.
- If their colors agree, paint that color. If different colors tie, leave the cell `0`.
- Example 0's diagonal/background boundary is exactly the equal-distance locus between the `8` and `9` sites.
- Example 1 confirms that two sites of the same color act as one color class, while ties against `7` remain zero.
- Example 2 confirms the rule with three colors and multiple pairwise tie cells.
