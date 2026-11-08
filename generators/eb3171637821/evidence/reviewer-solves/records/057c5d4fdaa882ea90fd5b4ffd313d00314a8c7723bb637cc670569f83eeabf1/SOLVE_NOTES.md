# Blind visible-only solve

This is an authored work summary, not a token-level conversation trace.
Earlier rule exposure: no. Reference or generator consulted: no.
Only the preparation output and public challenge were used.

## Observations and hypothesis

- Example 0: input 27 rows × 27 columns; output 3 rows × 5 columns.
- Example 1: input 27 rows × 27 columns; output 4 rows × 5 columns.
- Example 2: input 24 rows × 23 columns; output 4 rows × 4 columns.
- Each input has one color forming complete horizontal and vertical separator
  bands. The other color fills rectangular panels. Panel sizes and separator
  thicknesses vary, while the output records one pixel per panel.
- The proposed rule removes separator bands and collapses each remaining
  contiguous row band and column band to one representative cell. This also
  handles incomplete border framing and panels touching the image edge.

## Implementation and checks

Revision 1 identifies the lattice color through full rows and full columns,
then selects the first row and column of each nonseparator run. It does not
use color rank, panel area, or fixed input/output sizes. The official visible
checker will determine demonstration fit and record query execution without
revealing hidden-query correctness. No deliberately wrong attempt was made.
