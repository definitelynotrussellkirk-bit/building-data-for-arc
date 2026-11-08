# Solve work log

## Exposure declaration

Before this solve I had not opened the task's generator, canonical rule, reference
solution, private query labels, prior solve notes, or audit evidence. I used only
the visible examples printed by `review.py blind prepare` / `challenge.json`.

## Revision 1 — axis-aligned endpoint completion

**Observation.** Every non-background color appears exactly twice. In training
examples 0 and 1, pairs sharing a row or column have the zero-valued cells between
them recolored to make a solid segment. In training example 2, the vertical pair
is completed while a diagonal pair is unchanged. This separates an orthogonal
connection rule from a generic bounding-box or diagonal-line rule.

**Hypothesis.** For each nonzero color occurring exactly twice, fill every cell on
the inclusive horizontal or vertical segment when the two cells share a row or
column; otherwise leave that color unchanged. Segment length need not be exactly
three—the first test query visibly includes a longer horizontal gap, so the code
fills the entire interval rather than only a midpoint.

**Probe.** I created a local visible-example test that imports `solution.py` and
compares all three public training outputs. With the initial template it failed at
`NotImplementedError`, establishing the test. I then implemented the rule using a
copied grid and per-color coordinate groups.

**Alternatives rejected.** Filling a rectangle would alter the diagonal pair in
training example 2. Filling only a single midpoint would not define behavior for
the longer visible query gap. Connecting nearest unlike colors conflicts with the
fact that output segments retain each endpoint's own color.

**Remaining uncertainty.** The visible data does not define colors occurring more
or less than twice; the implementation conservatively leaves them unchanged. It
also assumes background is color 0, as in every visible example.
