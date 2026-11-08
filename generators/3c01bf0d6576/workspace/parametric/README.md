# Transform by example, then select in transformed coordinates

The episode parameter is `finish=transform_only|mark_first_after_transform`.
The default returns the selected canonical Racket source byte for byte. Both
settings first discover the nonzero components in bounding-box reading order,
infer the unique transform mapping A to A', crop B from the original input, and
apply that transform to B.

The composed setting then scans the transformed crop in row-major order, finds
the first nonzero cell, takes its color-blind four-connected component, and
recolors that component to 9. The selected component can change under the
inferred transform: the constructive B crops contain a connected main object
and an isolated top-right cell. Under a left-right flip the isolated cell moves
to the first position, while selecting before the flip marks the main object.
This supplies the required A -> intermediate -> B dependency rather than a
fixed-location paint.

`generate(seed, settings, demos=4, queries=4)` accepts exact seeds in
0..2**63-1, 4..6 demonstrations and 1..4 queries. It constructs the complete
six-demo/four-query bank before slicing. Inputs are identical across settings,
all ten are distinct, and the four-query bank is shuffled by a seed stream
independent of the demonstrations. The first four demonstrations include
multiple transform types, full-crop satellites, rectangular B crops and
vertical/staggered component layouts. The full bank covers all five supported
nonidentity transforms.

The input family ranges from 11x15 through 30x30. The 30x30 case touches all
four borders, places content in every quadrant, and uses a dense 12x12 B crop;
it is not a padded copy of a small scene. The exact canonical default remains
unchanged. Native qualification, public projection and causal witness evidence
are generated separately and remain source-bound; no training admission follows.
