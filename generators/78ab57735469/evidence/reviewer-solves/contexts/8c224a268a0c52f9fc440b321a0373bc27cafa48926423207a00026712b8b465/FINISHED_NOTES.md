# Solve work log

This is a human work log for the exposed post-repair solve. I had already seen
the task rule while repairing the generator, so this is not a blind inference
record. I did not consult the generator, Racket source, reference solutions, or
private query labels after `solve_episode.py prepare`.

## Visible-example reading

All three outputs are three input-width blocks across and three input-height
blocks down. The center block reproduces the input. In block columns 0 and 2,
the tile is reflected left/right; the middle block column keeps the original
column order. Independently, block rows 0 and 2 reflect the tile up/down; the
middle block row keeps the original row order. Therefore corner blocks apply
both reflections (a 180-degree rotation), edge-center blocks apply one, and the
center block applies none.

I checked this interpretation against asymmetric landmarks in all examples:

- train 0: the unique `4` at input (2,0) appears at the expected corner-block
  locations after both independent parity reflections;
- train 1: the unique `1` distinguishes left/right orientation inside the
  otherwise nearly symmetric frame;
- train 2: the `0` cells at (0,0) and (2,1) distinguish both axes.

## Implementation

For output coordinate `(row, col)`, let `br = row // n`, `bc = col // n`,
`r = row % n`, and `c = col % n`. Use `n-1-r` when `br` is even, otherwise
`r`; use `n-1-c` when `bc` is even, otherwise `c`. Return the resulting
`3n × 3n` grid.
