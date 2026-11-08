# Exposed solve notes — b9e736518d82

This is not a blind solve: I had already inspected the task rule while repairing the generator. During this solve episode I read only `solve/challenge.json` and did not reopen the generator, Racket source, reference solutions, or private labels.

## Visible-example hypothesis

The orange cells are walls around a one-cell-wide zigzag channel made of background cells (and sometimes one maroon marker). Candidate channel cells are 0/9 cells cardinally adjacent to orange.

- With no marker, the visible first example fills the larger relevant adjacent-orange component cyan.
- With a marker on a straight channel segment, the full channel is filled, including the marker.
- With a marker at a bend, removing the marker divides the channel into two path halves; only the larger half is filled, while the marker remains maroon.

I implemented the component order explicitly: in the no-marker case compare the row-major first component with the row-major first remaining component, matching the visible construction without relying on shape-specific coordinates. At a bend I compare the two components after removing the marker. No revision was needed because this rule explains all three demonstrations and handles both test branch types (one unmarked, one marked).
