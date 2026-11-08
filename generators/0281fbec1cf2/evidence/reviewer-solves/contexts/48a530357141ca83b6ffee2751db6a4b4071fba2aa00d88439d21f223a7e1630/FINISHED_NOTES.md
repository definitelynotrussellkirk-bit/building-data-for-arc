# Solve work log

## Isolation and exposure

I began from `solve-blind/challenge.json` only. I had not opened task
`0281fbec1cf2`'s generator, Racket rule, reference solutions, prior solve notes,
or private labels. I also had not opened the assigned repair generator before
this blind episode.

## Visible structure

Every example contains one solid red (`2`) rectangle plus a few isolated marker
cells (`4` or `8`). The output keeps the rectangle and markers, and projects the
rectangle as a cross: each rectangle row may extend horizontally to a border,
and each rectangle column may extend vertically to a border.

The extensions are independent rays. A marker aligned with a rectangle row or
column blocks only the ray on its own side:

- In training example 1, the marker above one rectangle column prevents that
  column's upward extension, while the same column still extends below.
- In training example 2, markers on both sides of the top rectangle row prevent
  both horizontal rays for that row, while the other rectangle rows extend.
- Markers not sharing a rectangle row or column do not affect the cross.

A "fill until the marker" interpretation was rejected: in training example 2,
the cells between each marker and the rectangle remain zero. The entire side-ray
is suppressed rather than stopping at the marker.

## Implementation hypothesis

Find the bounding box of all red cells. For each row in that box, fill the left
side only when it contains no nonzero blocker, and independently do the same on
the right. For each box column, apply the analogous rule above and below. Start
from a copy of the input so markers are preserved.

Before implementing, I made a local visible-example harness. It failed on the
provided `NotImplementedError`, as expected. After implementation, all three
visible training pairs matched exactly. Remaining uncertainty is limited to
unseen malformed inputs (for example, no red rectangle); the solver conservatively
returns a copy in that case.
