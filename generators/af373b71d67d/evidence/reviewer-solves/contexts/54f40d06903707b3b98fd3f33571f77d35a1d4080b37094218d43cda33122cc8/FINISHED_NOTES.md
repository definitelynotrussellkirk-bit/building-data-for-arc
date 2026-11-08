# Blind solve notes — af373b71d67d

I used only the visible examples in `solve-blind/challenge.json` / `README.md`.
I did not inspect generator code, canonical rules, private labels, prior solutions,
or audit material for this task.

## Hypothesis

Each input has a hollow rectangular frame in a nonzero color other than 3 and a
separate color-3 glyph. The output:

1. clears the source glyph;
2. rotates its tight bounding-box mask 90 degrees clockwise; and
3. places the rotated mask with its top-left at one cell down and one cell right
   from the frame's top-left corner.

The placement is not clipped to the frame interior. In visible example 0 the
rotated glyph is three rows tall while the interior is two rows tall, so its last
cell replaces a bottom-border cell. In visible example 1 the analogous overflow
replaces a right-border cell. Example 2 fits entirely inside and confirms the
same anchor and rotation without overflow.

## Probe plan

A local visible-pair regression test imports `solve()` and checks all three
training pairs exactly. The initial skeleton failed with `NotImplementedError`,
then the implementation was added.

## Limitations considered

The examples consistently reserve color 3 for the movable glyph. The solver
therefore treats every color-3 cell as the glyph and every other nonzero cell as
the frame. It assumes the generated placement remains within the grid, as all
visible examples do.
