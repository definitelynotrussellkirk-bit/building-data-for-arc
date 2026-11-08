# Blind solve work log — 17de34436a9f

This is an authored observation and experiment log, not a token-level model trace.
Before preparation I read only packet instructions and startup/resource tooling.
I had not opened this task's generator, Racket rule, notes, reference solutions,
audit evidence, or any other generator. The startup draw was resumed from its
original pending journal after an ENOSPC failure; no assignment was redrawn.

## Visible evidence and first hypothesis

All four visible inputs are 9 rows × 9 columns. Example 0 has a 3 × 2 output,
example 1 a 2 × 3 output, example 2 a 3 × 3 output, and example 3 a 3 × 2 output.
Each input contains one corner cell of color 9 and one differently colored object.
The output preserves the object's color and occupied-cell count and excludes 9.

Cropping the nonzero, non-9 cells directly matches example 0, whose marker is at
the top left. In example 1 the 3 × 2 crop must turn clockwise to make the 2 × 3
output; its marker is at the top right. The bottom-right marker in example 2
corresponds to a half turn. Example 3's bottom-left marker corresponds to three
clockwise quarter turns. This yields one shared rule: the corner index around
the image clockwise from top left selects 0, 1, 2, or 3 clockwise quarter turns.

I considered cropping alone as a simpler alternative, but it does not match the
three rotated visible outputs. No failed solver was submitted for that already
refuted alternative. The first actual implementation uses the shared corner rule.

## Revision 1

Implemented a tight object crop and the corner-selected rotation, without
using task lookup, reference code, canonical helpers, or query answers.
Validation command from the outer packet root:
`python3 review.py blind check --intent solve --note 'Crop the nonzero non-9 object and rotate clockwise by corner index TL=0 TR=1 BR=2 BL=3; all four visible examples support the mapping.'`

Only visible-example agreement and successful query execution can be checked here.
Masked-query correctness remains unknown until independent maintainer scoring.
