# Blind solve notes — 0281fbec1cf2

Human work log based only on `challenge.json`; no generator, rule, prior solution,
private label, or audit material was consulted.

## Hypothesis 1

The largest foreground component is a solid rectangle (color 2 in all visible
examples). The output fills the union of every row spanned by that rectangle and
every column spanned by it, producing a full-grid cross in the rectangle color.

Each smaller colored marker cuts exactly one lane of the cross on the side where
it sits:

- a marker above/below the rectangle leaves its aligned column background on that
  vertical arm only;
- a marker left/right leaves its aligned row background on that horizontal arm
  only;
- the marker itself is preserved.

This explains the asymmetric visible cases: an upper marker cuts only the upper
vertical arm, while the same column can still be filled below the rectangle; a
left marker cuts only the left horizontal arm, while the right side can remain
filled unless separately marked.

## Implementation probe

I identify the background by global frequency and the rectangle as the largest
4-connected non-background component, then apply the cross fill and marker cuts.
The implementation is intentionally not hard-coded to particular grid sizes,
rectangle dimensions, or marker colors.
