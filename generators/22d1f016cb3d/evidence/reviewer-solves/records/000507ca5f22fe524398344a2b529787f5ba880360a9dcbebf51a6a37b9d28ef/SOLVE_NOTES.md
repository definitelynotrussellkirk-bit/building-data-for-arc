# Solve work log

## Exposure declaration before solving

I had not opened task `22d1f016cb3d`'s generator, Racket rule, notes,
solutions, audit records, or private labels. I used only `challenge.json` and
my own local Python probe.

## Hypothesis 1

Every gray (`5`) cell is recolored from the shape of its orthogonal gray
neighborhood:

- four gray neighbors -> red (`2`), an interior cell;
- zero or one gray neighbor -> blue (`1`), an isolated/terminal cell;
- exactly two adjacent-direction gray neighbors -> blue (`1`), a corner;
- exactly two opposite-direction neighbors -> yellow (`4`), a straight segment;
- three gray neighbors -> yellow (`4`), an edge or junction.

All non-gray cells should remain unchanged. This explains both filled rectangles,
the internal hole (its adjacent cells become boundary yellow), and the one-cell-
wide vertical segment (blue endpoints, yellow middle).

## Probe

I ran an in-memory candidate against all three visible training pairs. It matched
all three exactly (`True, True, True`). I then encoded the same local rule in
`solution.py`. The two test inputs add a T-shaped gray component and non-gray
colors touching a gray rectangle; the rule predicts endpoint/corner blue,
straight/edge/junction yellow, fully surrounded red, while preserving the extra
colors.

## Remaining uncertainty

The examples do not explicitly demonstrate isolated gray cells, and the extra
colors in the second query do not occur in training. Preserving non-gray cells is
the least-assumptive extension because the demonstrated transformation targets
only gray cells.
