# Solve notes — final generator `ab6964be99e6…`

This is a human work log, not a captured model trace. I had earlier rule exposure from repairing this task, so this is not blind; I kept the generator, Racket source, prior solve directory, reference solutions, and private labels closed after `prepare`.

Visible-example check:

- Only color-1 components change. Colors 5/6/7/9 and background 0 are copied unchanged.
- Each example has three 4-connected color-1 objects with distinct occupied-cell counts.
- Sorting those counts ascending maps the objects to colors 2, 3, and 8 respectively.
- This explains all three visible examples even when the objects' positions and shapes differ, so I implemented a flood-fill plus cell-count ranking.

One ordinary solve attempt is sufficient unless visible checking finds a mismatch.
