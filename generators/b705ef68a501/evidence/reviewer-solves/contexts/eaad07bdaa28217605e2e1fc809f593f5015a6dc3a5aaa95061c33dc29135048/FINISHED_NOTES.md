# Blind solve notes — b705ef68a501

## Exposure

I used only the visible `solve-blind/challenge.json` / preparation output and local Python summaries of those grids. I did not inspect this task's generator, canonical rule, private labels, prior solutions, or audit records. Before the draw I accidentally opened the packet's generic `ARC-DESIGN.md`; it contains general authoring guidance but no task-specific information.

## Observations and hypothesis

Each grid contains several connected nonzero objects plus maroon (`9`) cells on the top row. Maroon can also form a larger distractor object (train 0), so I treat color 9 as the instruction color rather than a candidate.

The number of maroon cells on row 0 is a 1-based rank. Candidate objects are the 4-connected components whose color is neither 0 nor 9. Sort them by:

1. cell count ascending;
2. topmost row ascending;
3. leftmost column ascending.

Return the ranked component, cropped to its bounding box on a zero background.

Evidence:

- Train 0 has 3 top-row maroon cells. Candidate areas in order are 3 (color 7), 7 (3), 9 (6), 13 (1); rank 3 is the shown color-6 output.
- Train 1 has 2 maroon cells. Areas are 3 (6), 6 (8), 6 (4), 10 (2). The reading-order tie break puts color 8 second, matching the output.
- Train 2 has 3 maroon cells. Areas are 3 (5), 6 (3), 6 (8), 10 (1). The same tie break puts color 8 third, matching the output.

Predictions:

- Query 0: rank 1 selects the six-cell color-1 object (5×2 crop).
- Query 1: rank 2 selects the leftmost six-cell object, color 8 (2×4 crop).

## Alternatives rejected

I tested selection by marker geometry, nearest horizontal alignment, bounding-box dimensions, endpoint counts, and object symmetry. They failed at least one visible example. Area rank plus reading-order tie-breaking explains every visible output and resolves both equal-area demonstrations.
