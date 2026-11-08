# Solve notes

## Exposure declaration

I repaired this task's generator before this required solve, so I had earlier
rule exposure.  During this solve phase I used only the visible presentation and
did not reopen the generator, Racket authority, private labels, or prior solve
records.

## Visible-example hypothesis

1. Every black input cell remains black in the output.
2. Every cyan input cell becomes either red (`2`) or gray (`5`).
3. The distinction is vertical reflection across the horizontal midline: a cyan
   cell is red when the cell at the same column in the reflected row is cyan,
   and gray otherwise.
4. On an odd-height grid, the middle row is its own reflected row, so every cyan
   cell there must be red.

Visible checks: in train example 0, input `(0,0)` and `(11,0)` are both cyan and
both outputs are red.  Input `(0,9)` is cyan while `(11,9)` is black, so `(0,9)`
is gray.  This also refutes a left-right rule because `(0,0)` is cyan.  The
11-row example's all-black middle row is preserved, consistent with self-
reflection.

## Implementation

For each nonzero input coordinate `(r,c)`, inspect
`grid[height - 1 - r][c]`; emit `2` for cyan and `5` otherwise.  Emit `0` for
black.  The transformation preserves the input shape.
