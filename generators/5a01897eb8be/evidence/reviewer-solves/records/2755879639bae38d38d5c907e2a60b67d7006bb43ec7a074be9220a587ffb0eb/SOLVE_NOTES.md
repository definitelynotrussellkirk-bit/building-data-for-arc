# Visible-only solve notes

This is a human reasoning log over the public presentation produced by `review.py solve prepare`.
I had earlier rule exposure from repairing the assigned generator, so this is not a blind discovery record. During this solve episode I did not reopen the generator, Racket rule, canonical ledger, reference solution, or hidden answer.

Observed rule from the three visible examples:

1. The top-left value is the background. Treat every other color as one dispersed glyph; disconnected pieces of the same color belong together.
2. For each color, measure the maximum of its bounding-box height and width.
3. Also measure the longest same-color corner arm: at any cell, take the minimum of a horizontal run and a vertical run extending from that cell in any pair of perpendicular directions; keep the maximum.
4. Build concentric odd square rings. If a color has bounding-box size 1, use ring sizes `1,3,...`; otherwise use `3,5,...`. There is one ring per foreground color.
5. Assign non-exact (even/loose) sizes first to the smallest free ring that can contain them. Then assign exact odd sizes from largest to smallest, again using the smallest free ring that fits. This explains why a loose size can displace an exact glyph outward.
6. For each assigned ring, copy the measured arm to all four corners of that ring. Leave every other output cell background.

Checks against visible examples:
- Example 0: sizes 7,5,3,1 map directly to rings 7,5,3,1; the size-7 color has arm 3 and therefore leaves the midpoint of each outer edge blank.
- Example 1: no singleton color, so rings are 3,5,7; sizes 3,5,7 map directly.
- Example 2: six colors including a singleton give an 11x11 output with direct sizes 11,9,7,5,3,1.

Query expectations used by the implementation:
- Query 0 has one loose size-2 color. It takes ring 3; the exact size-3 color is displaced to the only later fitting ring, ring 11.
- Query 1 has one loose size-4 color. It takes ring 5; the exact size-5 color is displaced to ring 7.
