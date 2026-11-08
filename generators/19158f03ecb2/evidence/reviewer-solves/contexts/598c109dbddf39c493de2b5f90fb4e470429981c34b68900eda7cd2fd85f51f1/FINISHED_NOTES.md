# Solve work log

Earlier exposure before this blind episode: none to task `19158f03ecb2`'s rule,
generator, solutions, or audit records. I read only `solve-blind/challenge.json`.

## Revision 1 — horizontal reflection appended at right

Across all three training pairs the output height is unchanged and the width is
exactly doubled. In every output row, the left half equals the input row and the
right half equals that row in reverse column order. This holds for the 3×3,
8×9, and 7×5 examples, including asymmetric marker placements, so it is not a
simple duplication.

Hypothesis: for each row `r`, output `r + reverse(r)`, producing an even-width
left/right mirror with the seam between the original final column and its copy.

Probe: manually checked several asymmetric rows, including `[0,7,1]`, whose
output is `[0,7,1,1,7,0]`, and `[3,9,6,1,3]`, whose appended half is
`[3,1,6,9,3]`. These distinguish reflection from repeating the whole grid.

Alternatives considered and rejected: append an unchanged copy; reflect the
whole grid vertically; rotate 180 degrees before appending. All contradict at
least one visible row. Remaining uncertainty is limited to unseen metadata or
special cases not represented in the examples; the row-wise rule is otherwise
fully determined by the visible pairs.
