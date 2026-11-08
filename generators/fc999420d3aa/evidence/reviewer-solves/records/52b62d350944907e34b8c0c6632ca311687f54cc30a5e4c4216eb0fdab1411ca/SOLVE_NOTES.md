# Solve work log

## Exposure

Before this solve I had not opened the task's generator, Racket rule, reference
solution, private labels, audit material, or any prior explanation. I used only
the examples printed by `review.py blind prepare`.

## Revision 1 — complete T tetrominoes into plus signs

The changing objects are four-cell T tetrominoes: one center cell has three of
its four orthogonal neighbours occupied. Each output adds the sole missing arm
in the same colour, yielding a five-cell plus. Three-cell components are distractors
and remain unchanged, including both the L shapes in the demonstrations and the
three-cell vertical line in query 0.

The implementation finds 4-connected monochrome components. It changes only a
component of exactly four cells with a unique degree-three center, then fills the
single in-bounds background neighbour missing around that center. This avoids
changing arbitrary four-cell blocks, lines, or the three-cell distractors.

Predicted query changes:

- Query 0: add colour 9 at `(2, 9)` and colour 6 at `(5, 5)`; leave the
  three-cell colour-7 vertical line unchanged.
- Query 1: add colour 2 at `(3, 2)`.

The demonstrations do not show a T touching a border with its missing arm outside
the canvas. The code conservatively leaves such an impossible completion alone.
