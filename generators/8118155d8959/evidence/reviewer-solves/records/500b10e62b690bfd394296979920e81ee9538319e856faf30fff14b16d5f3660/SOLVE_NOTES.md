# Solve work log

## Prior exposure

I had not opened task `8118155d8959`'s generator, Racket rule, reference solution,
private labels, notes, or audit evidence. I used only the visible examples printed
by `python3 review.py blind prepare` and the files in `WORK/solve-blind/`.

## Revision 1 — rank gray components by area

The only changing cells are color-1 cells. In every training example they form
three 4-connected objects, while all non-gray colored objects remain unchanged.
The three gray-object areas and output colors are:

- example 0: areas 3, 4, 5 become colors 2, 3, 8;
- example 1: areas 2, 3, 4 become colors 2, 3, 8;
- example 2: areas 2, 4, 5 become colors 2, 3, 8.

This supports the rule: recolor the smallest gray object red (2), the middle-sized
object green (3), and the largest azure (8), preserving every other cell. Shape,
orientation, position, and the distractor colors vary across examples, so area
ranking is the common invariant.

I implemented plain-Python 4-connected component extraction, sorted the three
components by cell count, and applied `(2, 3, 8)` in ascending order. Both visible
queries also contain exactly three gray components with distinct areas, so the
visible evidence does not require a tie rule. The implementation uses top-left
coordinate only as a deterministic fallback if a tie occurs; tie semantics remain
uncertain because no visible pair demonstrates them.
