# Solve work log

I used only the visible challenge and local probes over its public grids. I had
not opened this task's generator, rule, private labels, reference solutions, or
any assigned-generator source before solving.

## Observations and hypothesis

The background is the dominant colour (5 in every visible example).  The output
is a crop around a compact non-square motif whose long side is four cells:

- examples 0 and 1 each contain two copies of the same 3x4 motif plus a singleton
  swatch of that motif's colour; the requested copy is the one containing one
  foreign-colour payload cell;
- example 2 has one compact 2x4 motif, so no duplicate disambiguation is needed;
- larger 4x9 corner shapes, 3x3 rings/blocks, and colour-7 markers are context.

I first made a visible-example harness and confirmed that the untouched template
failed with `NotImplementedError`.  I then implemented 4-connected same-colour
component extraction, selected compact components with a four-cell long side,
preferred a colour that also occurs as a singleton swatch, and preferred the copy
whose bounding box contains a foreign payload.  The returned grid is the original
bounding-box crop, so holes retain the background and payload colours are kept.

Remaining uncertainty: the public examples do not show a rotated 4x2/4x3 query,
but selection uses the long side rather than hard-coding output width, so those
orientations are handled.  The final row-order tie-break is only defensive and is
not needed by the visible examples.
