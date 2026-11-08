# Python solve work log

This is an assistant-authored experiment summary, not a token-level model trace,
log-probability record, or transcript of private reasoning. Earlier rule exposure:
**yes**. I had reviewed the task generator and reference during the preceding
repair. This solve is therefore not blind. After `solve_episode.py prepare`, I
read only `solve/challenge.json` and my own Python solution/test files. I did not
open generator code, Racket, reference solutions, prior explanations or private
answers during the solve.

## Visible observations and proposed implementation

The five demonstrations support extracting same-color orthogonally connected
components and ordering their bounding boxes by left column, then top row. In
example 2, two diagonal cells with color 9 appear as separate one-cell pieces;
one is ordered before the vertical color-7 component, the other after it.
Example 4 includes neighboring colors in the cropped rectangles. Example 1
places narrow crops in a width-five output with floor-centered padding. The
output inserts one zero row between pieces. I will implement that single rule
in standalone Python, with no project imports and no lookup table.

## Test setup

The visible-example tests are written before the solver. An initial failure
against the preparation stub is a deliberate test-harness red check, not a
wrong inferred rule or an independent failed solving attempt. Additional local
checks cover input immutability, repeated-color diagonal separation and malformed
input. These are implementation probes, not private-label feedback.
