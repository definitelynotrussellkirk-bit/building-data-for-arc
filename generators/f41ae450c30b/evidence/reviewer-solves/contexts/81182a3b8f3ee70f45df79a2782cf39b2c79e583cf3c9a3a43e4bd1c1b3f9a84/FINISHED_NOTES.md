# Visible-only solve work log

This is a human work log based only on `solve/challenge.json`. I had earlier rule exposure during generator repair, so this is not a blind solve; I did not consult the Racket rule, generator source, private labels, or previous solve explanations during this episode.

## Hypothesis from the three visible pairs

Each nonzero same-color 4-connected object is a domino. Sort objects by centroid column, then centroid row. Build an N×N matrix: object colors on the diagonal; 8 for an off-diagonal pair when some cells share a row or column and the segment between them contains only background or those two endpoint objects; otherwise 0. Thus a middle object blocks the two outer objects even though they remain aligned.

Visible evidence: in every collinear triple, adjacent pairs receive 8 while the outer pair receives 0. The isolated fourth object is connected only when it actually shares an unobstructed row or column.

## Predicted masked outputs

Test 1 object order: 6, 9, 5, 3. Predicted matrix:
`[[6,0,8,0],[0,9,8,0],[8,8,5,8],[0,0,8,3]]`.

Test 2 object order: 5, 2, 3, 4. Predicted matrix:
`[[5,8,0,0],[8,2,8,8],[0,8,3,0],[0,8,0,4]]`.

I will implement direct component extraction and line-of-sight rather than encoding these two cases.
