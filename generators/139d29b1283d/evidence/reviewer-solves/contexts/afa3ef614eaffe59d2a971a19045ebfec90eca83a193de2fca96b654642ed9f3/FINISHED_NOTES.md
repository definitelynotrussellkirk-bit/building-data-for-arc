# Post-repair visible-only solve work log

## Exposure and evidence boundary

This is the separate post-repair solve and is marked `earlier-exposure: yes`
because the task is exposed at team level. During this solve I read only the
current `solve/README.md` and `solve/challenge.json` as task evidence. I did not
open the generator, Racket rule, reference solutions, canonical helpers, private
labels, prior solution explanations, or other agents' files. No reference was
consulted during this solve. Earlier exposure is not being represented as a
fresh blind solve.

The challenge has three labeled training examples and two masked queries. The
queries' true outputs are unavailable. I did not execute the supplied stub or
record it as an attempted solve. The first checked program below is an actual
transformation hypothesis.

## Observations and initial hypothesis

Inputs have a single 1 marker, a single 2 marker, and one or more groups of
color-3 cells. The outputs are otherwise blank grids of the same size, with
color 8 in a few locations. The largest orthogonally connected color-3 group
appears to define a shape; smaller color-3 groups are distractors.

My hypothesis is:

1. Extract the largest orthogonally connected color-3 group.
2. Normalize its coordinates by subtracting its bounding-box top-left.
3. Place two copies, with their bounding-box top-lefts at the 1 and 2 markers.
4. On a blank grid, color only the intersection of the two copies with 8,
   retaining only cells inside the original grid.

I arrived at this by aligning the largest shapes to the marker positions in
the visible examples. The following coordinates are zero-based.

- Training 0: the largest group has 8 cells, with normalized coordinates
  `(0,2), (0,4), (1,0), (1,1), (1,2), (1,3), (1,4), (2,1)`.
  Placing it at markers `(5,6)` and `(6,6)` gives intersection
  `{(6,8), (6,10), (7,7)}`, exactly the three visible output cells.
  The other color-3 components have 5 cells and 1 cell.
- Training 1: the largest group also has 8 cells, with normalized coordinates
  `(0,2), (1,0), (1,1), (1,2), (1,3), (1,4), (2,2), (2,4)`.
  Placing it at `(2,6)` and `(1,7)` gives intersection
  `{(2,8), (3,9)}`, exactly the two visible output cells. The smaller
  color-3 group has 5 cells.
- Training 2: the only color-3 group has 5 cells. Its normalized width is 3.
  Copies placed at `(1,1)` and `(0,7)` have disjoint column ranges, so their
  intersection is empty, matching the blank visible output.

This explanation accounts for the shapes, output color, marker roles, removal
of the input objects, and the empty case with one operation. I have not tested
or rejected any alternative implementation, and I have not manufactured a
failing attempt.

## Actual implementation revision 1

I implemented the hypothesis directly in `solution.py`: collect color-3
orthogonal components, select the largest, translate its normalized shape to
each marker, and render the set intersection as color 8. The function creates
a new output grid and does not modify its input. It contains no example or
query lookup and no input-specific special case.

The check uses the activated `.venv` and the complete visible-example gate.
It also checks execution; it does not reveal private query correctness.

Command:

```sh
source .venv/bin/activate
python3 solve_episode.py check --intent solve --note 'Place copies of the largest orthogonally connected 3-shape at markers 1 and 2, then render only their intersection as 8; the visible coordinate alignments explain all three training outputs.'
```

Observed result: command exit 0. Checker revision 1 reported
`execution_status: completed`, `visible_passed: 3`, `visible_total: 3`, and
`reported_label: unknown`. The program hash was
`19310828d2e83ca06e2de85db294c4c86c06f0c0121564cab8a0347a73d667f9`.
This is one actual hypothesis implementation and one official check; no
diagnostic or stub attempt was submitted.

## Stopping decision and uncertainty

The implementation reproduces all three visible examples, including the
empty-intersection case, and the coordinate reasoning explains the observed
nonzero outputs exactly. I made no further solution revision after this
check. I stop here because no concrete visible discrepancy remains to resolve.

The two masked query outputs remain unverified. The `unknown` reported label
must not be interpreted as correctness feedback for those queries. The visible
examples do not establish behavior for every possible ambiguity, such as two
equally large candidate components; the implementation uses a deterministic
row-major selection in that unobserved case.

Finish command, retaining the honest earlier-exposure declaration:

```sh
source .venv/bin/activate
python3 solve_episode.py finish --earlier-exposure yes --reference-consulted no --reason 'The shape-copy intersection hypothesis passed all 3 visible examples on its first actual implementation; the empty case is explained, and masked-query correctness remains unknown.'
```

The official check preserves revision 1 and its work log. Finishing freezes
this complete human-readable log as well. No task source or reference was
opened during the solve.
