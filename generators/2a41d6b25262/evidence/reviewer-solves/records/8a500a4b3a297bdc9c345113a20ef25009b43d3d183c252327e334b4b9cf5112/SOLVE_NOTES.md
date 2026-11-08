# Visible-only solve notes

## Observations

Each input has a zero background, one blue (`1`) cell, one red (`2`) object,
and one green (`3`) object. The output removes the input objects and contains
only cyan (`8`) cells near the blue cell's former position.

Absolute source positions and reading order change, so the source objects must
be compared as shapes rather than copied at their original locations. For each
source color I translated its occupied coordinates so its own top-most row and
left-most column become zero.

## Hypothesis

Take the symmetric difference (XOR) of the two independently normalized source
supports: keep offsets occupied by exactly one source shape. Stamp those offsets
at the blue cell on an otherwise empty output grid. Do not crop or normalize the
XOR after computing it; examples with an empty leading row or column preserve
that offset relative to the marker.

## Checks against the visible demonstrations

- Demonstration 1: the independently normalized four-cell sources share some
  offsets; the four exclusive offsets match the four cyan output cells.
- Demonstrations 2–4 vary object sizes, source order, and marker location while
  preserving the same normalize/XOR/stamp construction.
- Union would retain shared offsets, intersection would omit exclusive offsets,
  and re-cropping the XOR would shift at least one visible output, so those
  alternatives do not fit all demonstrations.

The implementation gathers colors 2 and 3, normalizes each, XORs their offset
sets, and writes color 8 at marker-plus-offset. This is a human work log based
on the visible challenge. I had earlier rule exposure during the required
generator review and will declare that honestly at finish; I did not consult a
reference while writing this solve.
