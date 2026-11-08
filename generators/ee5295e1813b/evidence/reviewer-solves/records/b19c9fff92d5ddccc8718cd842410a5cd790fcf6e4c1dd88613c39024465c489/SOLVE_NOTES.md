# Solve notes: ee5295e1813b

## Visible evidence

Each output preserves the input shape and every existing colored cell. The only changes are blank interior cells centered in a 3×3 pattern whose four diagonal corners are one identical nonzero color:

- train 0 fills centers `(1,5)=2` and `(2,2)=8`;
- train 1 fills `(1,4)=2`, `(6,3)=2`, and `(6,6)=2`;
- train 2 fills `(2,3)=9` and `(6,5)=9`;
- train 3 fills one center for each of colors 8, 3, and 5;
- train 4 fills the centers of the two complete 7-corner patterns while leaving the incomplete 9 pattern unchanged.

## Hypothesis

For each originally blank interior cell, inspect northwest, northeast, southwest, and southeast. If all four are equal and nonzero, copy that color into the center. Otherwise leave the cell unchanged. All decisions use the original input rather than newly filled output cells.

## Alternatives rejected

- Global color frequency is insufficient: examples contain incomplete and unrelated colored structures, while the changed cells are determined locally.
- Three matching corners are insufficient: incomplete 9/5 structures remain unchanged.
- Orthogonal neighbors are not the trigger; changes consistently use diagonals.
- Filling only one center per color is contradicted by train 1 and train 4, where the same color fills multiple centers.

## Query expectations

Query 0 should fill every complete 1-corner center and leave the incomplete/mixed 5 context unchanged. Query 1 should fill the complete 8 and 4 diagonal centers and preserve the mixed lower-left structure. The implementation scans all interior cells against the unmodified input.
