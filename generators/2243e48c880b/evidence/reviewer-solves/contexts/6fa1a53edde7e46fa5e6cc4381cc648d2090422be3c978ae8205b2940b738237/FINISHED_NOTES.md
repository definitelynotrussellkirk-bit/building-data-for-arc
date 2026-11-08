# Blind solve work log

I had earlier exposure to this task's visible-example pattern in an interrupted review attempt, so this is not a first-exposure solve. I did not consult any generator, canonical rule, reference solution, or private label during this episode.

The visible grids contain exactly three monochrome 4-connected objects. The output preserves their cells and recolors the objects after sorting by increasing area. Equal-area objects are ordered by their first occupied cell in reading order. The resulting ranks receive colors 2, 4, and 8.

Current examples confirm the rule:
- Example 0 has areas 3, 3, and 6; the equal area-3 components are colored 2 then 4 in reading order, and area 6 becomes 8.
- Example 1 has areas 4, 5, and 5; area 4 becomes 2, then the two area-5 components become 4 and 8 in reading order.
- Example 2 has areas 4, 5, and 6 and maps directly to 2, 4, and 8.

One implementation revision matched all visible examples, so I stopped.
