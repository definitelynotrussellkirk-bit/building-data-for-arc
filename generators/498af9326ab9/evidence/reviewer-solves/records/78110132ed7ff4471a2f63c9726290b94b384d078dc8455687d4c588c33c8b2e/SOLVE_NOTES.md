# Solve work log

## Prior exposure

Before this blind solve I had not opened task `498af9326ab9`'s generator, Racket
rule, notes, reference solutions, private labels, or audit records. I read only
`solve-blind/challenge.json` plus the solve template and packet instructions.

## Hypothesis

The colored cells `1` and `2` are endpoints, color `5` is an impassable wall,
and color `8` marks the union of all shortest four-neighbour paths from `1` to
`2`. Existing nonzero cells are preserved. This explains:

- the direct horizontal band when no wall intervenes;
- the single lower detour when that route is shorter than going above;
- both upper and lower detours when they tie; and
- the two side detours around a hollow rectangle, while its sealed interior
  remains uncolored because no endpoint-to-endpoint path can enter it.

An equivalent test for a traversable cell `x` is
`dist(1, x) + dist(x, 2) == dist(1, 2)`, with distances computed while treating
`5` as blocked.

## Probe and implementation

I first imported the untouched template and checked it against the first visible
training pair. It failed with `NotImplementedError`, as expected.

I then implemented two breadth-first searches, one from each endpoint, and colored
only zero-valued cells satisfying the shortest-path equality. This avoids
hard-coding orientation, obstacle shape, or which side of an obstacle is closer.

## Alternatives considered

A bounding-box fill around the endpoints and obstacle fits some examples but not
the asymmetric case, where only the shorter lower route is colored. A rule that
selects one arbitrary detour also fails the symmetric examples, which retain both
equally short routes. The all-shortest-path interpretation accounts for all three
visible pairs without special cases.

## Remaining uncertainty

The visible data contains one `1`, one `2`, gray obstacles, and background zero.
The implementation therefore treats all colors other than `5` as traversable but
only recolors zero. If hidden instances introduce multiple endpoints or a
separate traversable decoration, the intended convention is not demonstrated.
