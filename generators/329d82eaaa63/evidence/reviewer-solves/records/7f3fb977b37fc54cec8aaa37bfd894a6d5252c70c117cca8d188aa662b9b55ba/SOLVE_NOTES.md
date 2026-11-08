# Solve work log

## Prior exposure

This is the required post-repair solve. I had already reviewed the assigned
generator and canonical authority before this episode, so earlier rule exposure
is **yes**. During this solve I did not consult the Racket rule, generator
source, reference solutions, or private query labels; I used the three visible
training examples printed by `solve_episode.py prepare`.

## Revision 1 — alternating straight and split rows

**Observation.** Every nonzero input cell is a seed on row 0. In every output,
the same seed color appears at its original column on rows 0, 2, 4, ... . On
rows 1, 3, 5, ... the color appears one column to the left and one to the
right, leaving the original column zero. The 15-row single-seed example shows
that the alternation continues beyond the six canonical rows; the three-seed
example shows the operation applies independently to every seed.

**Implementation.** Allocate a zero grid with the input dimensions. Read all
nonzero cells from the top row. For each output row, place each seed at its own
column when the row index is even, otherwise place it at the two adjacent
columns. Boundary checks make the function defined even for an edge seed,
although the visible examples keep enough margin for both branches.

**Alternatives rejected.** A fixed six-row template is contradicted by training
example 2. Copying only the first seed is contradicted by training example 1.
Straight vertical lines and one-sided diagonals both contradict every odd row.
