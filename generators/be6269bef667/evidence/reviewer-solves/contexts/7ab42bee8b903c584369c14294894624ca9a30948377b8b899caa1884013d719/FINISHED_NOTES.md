# Post-repair visible-only solve notes

This is a human-authored work log based only on the visible examples printed by `solve_episode.py prepare`. I had earlier rule exposure during generator repair, so this is not a blind solve; I did not reopen the generator, Racket source, private labels, or previous solution explanations after preparation.

## Hypothesis

The input symbols are directional ray emitters and blockers:

- `1` sends a ray upward.
- `2` sends a ray rightward.
- `3` sends a ray downward.
- `4` sends a ray leftward.
- `5` is a wall.
- `0` is empty background.

The output is a fresh all-zero grid of the same shape. Each emitter contributes one to every traversed cell, including its own cell. A ray passes through other emitters, but stops before a `5` wall or when it leaves the grid. Overlapping rays add, explaining output values 2 and 3.

## Visible checks

- Train 0: the `2` at row 5, column 0 sweeps right across row 5; the `4` at row 5, column 7 sweeps left. Their overlap gives 2 across most of the row. Vertical rays crossing at column 3 raise one cell to 3.
- Train 1: the `3` at row 0, column 5 stops before the wall at row 3, column 5, matching the zero at the wall and the resumed unrelated upward contribution below it.
- Train 2: multiple vertical and horizontal rays overlap at rows 4–5, producing the displayed 2s and 3s. Color-5 cells themselves remain zero unless crossed by no ray because rays stop before them.

## Implementation decision

Use direct simulation from each emitter. Do not mutate the input. The implementation is shape-preserving and handles any rectangular grid with these symbols.
