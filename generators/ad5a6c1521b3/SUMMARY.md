# ad5a6c1521b3

Use the unique modal background. For every other color independently, find its
4-connected components. A color with only one component is unchanged. If a
color is split, choose the largest component; equal sizes are resolved by the
component whose top-left corner has the greatest row-plus-column value (the
lower/right component). Erase every cell of that color, then fill the winner's
entire bounding rectangle plus the immediately adjacent column on its left.

The four-profile curriculum covers 8×8 and 16×16 canonical shape/palette
profiles, equal-size lower/right ties, unique winners that are not always
lower/right, two colors transformed in one scene, three-component cases,
passive one-component distractors, irregular winners whose holes must be filled,
and a visible left expansion column.
