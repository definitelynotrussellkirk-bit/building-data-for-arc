# Solve work log

## Exposure declaration

Before this solve I read only the packet-level welcome/return instructions and the
printed assignment. I did not open task `779887a0f354`'s generator, Racket rule,
reference solution, private labels, prior solve notes, or review records.

## Observations and hypothesis

The yellow cells behave like non-opaque rooks. A background cell becomes red when
at least two yellow cells share its row or column. A yellow cell can itself become
red, but only when at least two *other* yellow cells align with it. This explains:

- a row with exactly two yellow cells becoming red everywhere except at those two
  cells;
- a rectangle's four yellow corners becoming red because each corner sees one
  yellow horizontally and one vertically;
- off-line cross intersections becoming red when one yellow contributes a row ray
  and another contributes a column ray.

Gray cells are opaque blockers. The decisive witnesses are training example 2 at
row 1, column 2 and training example 5 at row 9, column 9: each would receive two
rays under unrestricted alignment, but a gray cell lies between it and one yellow,
so it remains background. Yellow cells do not block other yellow rays; the row with
three yellows in training example 5 proves that all three original positions have
two other aligned yellows and therefore turn red.

I model each row and column as segments separated by gray cells. For every non-gray
cell, I count yellow markers in its row segment and column segment. For an original
yellow cell I subtract its two self-counts. The output is red exactly when the
remaining total is at least two; all other cells are background.

## Test-first probe

I first ran a local visible-example harness against the untouched stub. It failed
with `NotImplementedError`, establishing the red test. I then implemented the
segment-count rule and reran the same harness against all five visible examples.

## Remaining uncertainty

The examples do not distinguish whether some unseen blocker color besides gray
would also stop rays, but only colors 0, 4, and 5 occur. They also do not test an
empty grid or ragged rows; the challenge uses rectangular nonempty ARC grids.
