# Solve notes — human work log

This is a human work log, not a captured model transcript or token-level trace.
I had already seen the task rule while repairing the assigned generator, so this
solve is **not blind**. During the fresh solve phase I consulted only
`solve/challenge.json` and visible-example execution feedback; I did not reopen
the generator, Racket rule, reference solutions, or private labels.

## Visible structure

Every input has four full-height color-9 separators and therefore five panels:

1. a narrow key,
2. a four-column candidate output,
3. a second narrow key,
4. a second four-column candidate output,
5. a wider query field.

The target is always one of the two candidate-output panels after removing its
vertical zero padding.

## Hypothesis and probes

Across the five demonstrations, the selected candidate is paired with the key
that occurs in the query at the same orientation. The fifth demonstration is
the decisive probe: the first key appears with extra colored cells in positions
where the key contains zero. It still selects candidate 1. Therefore nonzero key
cells are constraints while zero key cells are wildcards; strict equality of the
whole key bounding box is a rival rule refuted by that example.

I manually checked both branches:

- demonstrations 1 and 5 select key/candidate 1;
- demonstrations 2–4 select key/candidate 2;
- rotated and one-cell-near key-shaped distractors do not count;
- the two masked test inputs visibly contain key 1 and key 2, respectively.

## Implementation

`solution.py` discovers separator columns rather than hard-coding dimensions,
crops the four definition panels to their nonzero bounding boxes, scans the query
for each key with key-zero wildcard semantics, and returns the uniquely selected
candidate. No intentional teaching negative or fabricated failed attempt was
created.
