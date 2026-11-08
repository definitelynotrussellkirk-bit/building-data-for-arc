# Post-repair solve work log: bee63e6e52bd

This is a concise model-authored work log, not a token-level conversation trace.

## Exposure disclosure

The review-level finish declaration is `earlier-exposure yes`: the root review
actor inspected the rule during the preceding repair work. This separate solver
actor has not read that rule, generator code, task notes, canonical data,
reference implementations, previous solution explanations, or audit evidence.
No rule details were supplied to this solver. I used only the public solve
README/challenge, the solution/work-log files, my own Python analysis, and
visible checker output. Reference consultation during this solve is `no`.
This is the required exposed post-repair review record, not a claim that the
whole review had no earlier exposure.

## Preparation

From the outer packet directory:

```sh
WORK/.venv/bin/python review.py solve prepare
```

The command exited 0. It displayed three demonstrations, all with input and
output shapes 9 by 9. The two query inputs were 7 by 7 and 9 by 9; their
outputs were unknown. Preparation bound the episode to generator SHA-256
`33d8f354812b25e8e5afe7555c6296040b7d63e0b6315dea5a184c5515227b3f`.

## Observations and hypothesis

Every input contains one monochromatic rectangular frame with a contiguous
opening on one side. The output preserves every existing colored cell and adds
color 4. In coordinates parallel to the opening, the added yellow has three
parts:

1. Inside the frame, fill the opening's span expanded by one cell at each end.
2. Through the opening and outward to the grid edge, continue its original
   span as a straight beam.
3. Outside the frame, draw two one-cell diagonal rays. At outward distance d,
   their transverse coordinates are opening_start - d and opening_end + d.

The third demonstration is decisive for the interior: its frame occupies
rows 0 through 7 and columns 5 through 8; the left opening covers rows 1
through 4. Yellow fills interior rows 1 through 5, but cells (6, 6) and
(6, 7) stay zero. Therefore filling the entire frame interior is inconsistent
with this demonstration. The one-cell expansion of the opening fits it and
also fits the other two demonstrations.

The exterior is a straight strip plus diagonal boundary rays, not a fully
filled widening triangle: in demonstration 1, row 8 has yellow at columns
1, 2, 3, and 5, while columns 0 and 4 remain zero.

## Visible-only geometry experiment

A Python heredoc reading only `solve/challenge.json` computed nonzero bounding
boxes, incomplete sides, and visible yellow/zero coordinates. It exited 0.
It found:

- Demonstration 0: box (top, left, bottom, right) = (2, 0, 8, 6), right
  opening rows 4..6, and 38 added yellow cells.
- Demonstration 1: box (3, 0, 6, 4), bottom opening columns 1..3, and
  18 added yellow cells.
- Demonstration 2: box (0, 5, 7, 8), left opening rows 1..4, and
  39 added yellow cells; the two interior zero cells above remain unfilled.
- Query 0: box (3, 0, 5, 6), top opening columns 3..5.
- Query 1: box (4, 1, 7, 7), top opening columns 3..5.

The query observations describe only their inputs. Their correctness was not
tested against any answer. Applying the geometry to the previously unseen top
orientation assumes that the demonstrated transformations rotate consistently.

## Revision 1

Implemented the three geometric parts using outward distance and transverse
coordinates, handling all four opening orientations. The program copies the
input, changes only zero cells to 4, and rejects multiple open sides or a
noncontiguous opening because those cases are unspecified by the examples.
All supplied inputs satisfy the observed single-frame structure.

This is the first attempted implementation. No failed implementation or
deliberately wrong teaching negative was manufactured.

The official check command was:

```sh
WORK/.venv/bin/python review.py solve check --intent solve --note 'Infer a rectangular frame with one opening: add a straight yellow beam and outward diagonal rays, and fill the interior only within the opening span expanded by one cell; the asymmetric third demonstration excludes filling the full interior.'
```

It exited 0 and recorded revision 1 with intent `solve`, execution status
`completed`, visible results `3 / 3`, and reported label `unknown`.
Program SHA-256:
`058595c88735be2b4ac43fdce5711a0e6cd66277fcdb742450a3a8c714412125`.
No code revision was needed after that check.

## Stopping decision

I am finishing because the first implementation exactly matches all three
visible demonstrations, including the asymmetric interior and sparse exterior
rays, and the checker completed execution. Query predictions use the same
geometry rotated to a top opening, but hidden query correctness remains
unknown. Finish declares earlier exposure `yes` at the review level and
reference consulted `no`, as explained above.
