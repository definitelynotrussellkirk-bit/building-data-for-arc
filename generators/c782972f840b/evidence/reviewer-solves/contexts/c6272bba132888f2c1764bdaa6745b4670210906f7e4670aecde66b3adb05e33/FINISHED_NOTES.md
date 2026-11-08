# Solve work log

Earlier exposure: none. I had not opened task `c782972f840b`'s generator, rule,
notes, solutions, audit records, or private labels. I used only
`solve-blind/challenge.json` and local Python experiments over that JSON.

## Observations and hypotheses

The output side length equals the number of non-background, same-colour,
4-connected objects, ordered by the first occupied cell in row-major order. The
matrix is symmetric and uses 9 on the diagonal. I first considered pairwise
pixel overlap, Hamming distance, spatial distance, and relative orientation.
Those ideas failed on repeated shapes and on mirror-image S/Z tetrominoes: the
same geometric pair could receive different values depending on colour, while
same-colour pairs always gained 2.

Splitting each off-diagonal value into independent bits explained every pair:

- add 2 when the two objects have the same input colour;
- add 4 when their cropped binary shapes are equivalent under rotations only
  (0, 90, 180, or 270 degrees), not reflection;
- otherwise add neither; replace every self-comparison by 9.

This predicts all four possible off-diagonal values: 0, 2, 4, and 6. A useful
counterexample against treating mirror images as equivalent is the vertical S
versus vertical Z pair in the first lesson: they share a colour but are not
rotation-equivalent, so the value is 2 rather than 6. A useful positive witness
is the two identical horizontal S shapes: same colour plus rotational
congruence gives 6.

## Probe

I extracted components from the visible examples, cropped them to binary masks,
and checked all four rotations for every pair. The resulting matrices matched
all three training outputs exactly. The final program implements that rule with
standard Python only. No Racket reference or private query answer was consulted.
