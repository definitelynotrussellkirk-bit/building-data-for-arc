# Solve notes — cefd2849a551

## Visible-example hypothesis

Every input contains one monochrome nonzero shape on background 0.  The output
keeps the same canvas and color, but removes cells that are surrounded on all
four orthogonal sides by the same shape color.  Equivalently, the output is the
shape's 4-neighbor boundary.  Diagonal exposure alone is not enough to retain a
cell: train example 2 contains concave geometry that distinguishes a
4-neighbor boundary from an 8-neighbor boundary.

## Probe against the examples

- Train 0: the 4×6 rectangle loses its 2×4 orthogonal interior and retains a
  16-cell perimeter.
- Train 1: the irregular lower-right extension is preserved where exposed, and
  the four cells with all four same-color cardinal neighbors are removed.
- Train 2: the top block and narrow stem are processed as one connected shape;
  cells beside the concave junction stay or disappear according to cardinal,
  not diagonal, exposure.

## Implementation choice

For each nonzero cell, inspect north, south, west, and east.  Copy the cell to a
fresh zero grid when at least one neighbor is outside the canvas or has a
different value.  This also handles multiple colors/components without joining
them, although the visible instances contain one object.

No generator, Racket rule, private label, or reference solution was consulted
during this solve episode.  I had prior rule exposure from the required repair
work and will record that honestly at finish.
