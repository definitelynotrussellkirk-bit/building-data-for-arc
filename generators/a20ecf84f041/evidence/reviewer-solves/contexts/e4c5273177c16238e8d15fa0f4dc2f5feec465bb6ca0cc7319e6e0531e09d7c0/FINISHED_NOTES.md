# Blind solve notes

The grid is divided by color-9 lines into a 2-by-3 array of equal panels.
The upper row is a complete worked example: two colored binary masks and a
color-2 result mask. Across the three training examples, that result is,
respectively, the cellwise OR, XOR, or AND of the first two panels. The lower
right panel is blank, so the task is to infer the Boolean truth table shown in
the upper row and apply the same cellwise operation to the two lower masks.

I implemented the more general version rather than naming OR/XOR/AND: collect
the demonstrated mapping `(left occupied, middle occupied) -> result occupied`
from every upper-panel cell, check it is consistent, and use it below. This also
preserves the full grid and the demonstrated result color.
