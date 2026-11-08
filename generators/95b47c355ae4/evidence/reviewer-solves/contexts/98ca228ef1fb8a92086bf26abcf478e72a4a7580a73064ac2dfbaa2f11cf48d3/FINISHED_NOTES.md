# Solve notes

The three visible demonstrations preserve every gray `5` and move every magenta
`6` exactly one row down and one column right. The original `6` position becomes
background. This is visible on both source parities and both column parities:
for example, train 0 has `(0,0)->(1,1)` and `(5,5)->(6,6)`, while train 1 has
`(0,7)->(1,8)` and `(4,2)->(5,3)`.

Implementation plan: record all original `6` coordinates, erase them, then paint
at `(r+1,c+1)` when in bounds. Recording first avoids cascading a newly painted
cell. All non-6 cells remain unchanged.

This is the required exposed post-repair solve. I had earlier rule exposure from
the generator review, but during this solve I used only the displayed examples
and did not consult the Racket rule, generator source, private labels, or prior
solve notes.
