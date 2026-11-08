# Blind solve notes — 4a6d26e0b6ae

## Hypothesis
Each nonzero colour occurs exactly twice. The two cells are aligned horizontally or vertically with exactly one background cell between them. The output fills that midpoint with the same colour, turning each pair into a contiguous length-three segment. All other cells remain unchanged.

## Evidence from visible examples
- Example 0 contains four horizontal pairs; each midpoint alone is filled.
- Example 1 contains three vertical pairs; each midpoint alone is filled.
- Example 2 returns to horizontal pairs and applies the same rule.
- The queries contain both horizontal and vertical pairs, so the implementation handles both orientations independently per colour.

## Revision 1
Implemented the direct midpoint rule. No generator, canonical rule, private labels, reference solution, or audit evidence was consulted.
