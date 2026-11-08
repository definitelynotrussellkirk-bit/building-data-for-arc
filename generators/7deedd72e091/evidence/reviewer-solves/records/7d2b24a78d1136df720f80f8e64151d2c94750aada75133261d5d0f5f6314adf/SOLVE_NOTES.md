# Visible-only blind solve notes

## Scope and exposure

I read only this lane's `README.md` and `challenge.json` before writing the
solver. I have not read the generator, Racket rule, canonical/reference
solution, private labels, audit evidence, or earlier solution explanations.
There was no earlier rule exposure or reference consultation.

The parent later supplied an independent hypothesis based on the same public
examples: compare shapes up to translation and dihedral transforms, and encode
the odd panel. My own match-matrix interpretation and rotation/reflection probe
preceded that message. I considered the parent's translation suggestion but
did not implement translation, for the reasons below. This is collaborative
visible-only reasoning, not reference access.

## Observations and hypothesis

- Columns 3 and 7 consist of color 9 and separate three 3-by-3 panels.
- Every output is a symmetric 3-by-3 matrix with 8 on the diagonal.
- The nonzero off-diagonal pair identifies two panels whose binary masks match
  after rotating the full panel. Their paint colors may differ.
- The matching panel pairs are 0/1, 0/2, and 1/2 in training examples 0, 1,
  and 2 respectively.

The implemented rule ignores nonzero paint color, preserves the full panel
frame including empty rows and columns, and canonicalizes each mask over four
quarter-turn rotations. Output entry (i,j) is 8 exactly when panel i and panel j
have the same canonical mask; otherwise it is 0.

## Actual probes before implementation

I first compared full binary masks under rotations alone and under rotations
plus reflections. Both variants reproduced all three visible training
outputs. This corrected my initial impression that the third example needed
a reflection: a subsequent probe found these clockwise rotations directly:

| Visible example | Matching panels | Quarter turns |
| --- | --- | --- |
| 0 | 0 to 1 | 2 |
| 1 | 0 to 2 | 3 |
| 2 | 1 to 2 | 3 |

Both probe commands exited with status 0. They read only the visible
`challenge.json` and printed results for the training pairs. There was no
failed `solution.py` revision; the probes were hypothesis comparisons before
the first implementation, not manufactured negative submissions.

## Ambiguities and implementation choice

The visible training pairs do not distinguish rotations from all dihedral
transforms. I selected the narrower sufficient rule, quarter-turn rotations.
They also do not prove whether translation should be ignored. I retained the
full panel coordinates because the equal-sized frames provide those
coordinates and no training match requires trimming. In visible query 1,
trimming each shape would make all three panels equivalent L triominoes,
whereas preserving the frame distinguishes the panel containing the center
cell. That illustrates an unresolved inference choice, not known query
correctness.

## Revision 1

The first implementation parses color-9 separator columns, compares full
binary masks modulo rotation, and emits their pairwise equivalence matrix.
It uses only Python's standard library features. I will run the required
visible check for this revision and retain the masked-query uncertainty.
