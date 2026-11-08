# Visible-only blind solve work log

Task: cdb267535df8. I have not consulted a rule, generator, reference solution,
private label, prior solution explanation, task note, or audit. I have had no
earlier rule exposure. Task-specific evidence used so far is the output from
`python review.py blind prepare`, `WORK/solve-blind/README.md`, and
`WORK/solve-blind/challenge.json`.

## Preparation

From `/workspace/scratch/e654845a1e93/review_packet`, ran:

`python review.py blind prepare`

Exit code: 0. It exposed three labeled training examples and two test inputs
with unknown outputs. No hidden query labels have been consulted.

## Revision 1: shortest paths with color ties

Observed evidence:

- Gray (5) cells are preserved in every training output.
- Every other initial nonzero cell is preserved and appears to be a color seed.
- In training example 0, the right-side blank row 2 is equidistant from blue
  (0, 8) and orange (4, 8). On the left, (2, 0) and (3, 1..4) are also
  equidistant from the two nearby seed colors and remain blank.
- Barriers require detours: the orange/azure diagonal in the lower-right of
  example 0 is consistent with paths through different holes in the gray cross.
- Gray rings in examples 1 and 2 enclose zeros that remain blank, supporting
  four-neighbor motion rather than diagonal motion.
- Multiple seeds can share a color. A tie between same-color seeds should
  still receive that color; only equal distances to different colors remain 0.

Hypothesis: For each seed color, calculate the shortest four-neighbor distance
from any seed of that color while treating gray cells as impassable. Fill each
zero with the uniquely nearest color. Leave ties between colors and unreachable
cells zero. Preserve all originally nonzero cells.

Implementation: A breadth-first search per color, followed by the minimum
distance comparison at each initially zero cell. This uses only the input grid
and no example-specific coordinates or outputs.

Planned official test:

`python review.py blind check --intent solve --note 'Revision 1: four-neighbor shortest-path fill around gray barriers; equal-distance ties between distinct seed colors remain zero, matching the visible boundaries and enclosed blanks.'`

Result: pending. This is the first actual solution revision; there are no
earlier failed revisions to retain.
