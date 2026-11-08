# Legend-directed object counts

## Reference and input grammar
All three public demonstrations and the supplied test gold are reproduced by the
reference. The black rectangle is the output-chart template. Each nonblack seed
labels a row. Mask that rectangle, segment same-color eight-connected external
objects, count them by legend color, and repeat each row's seed at two-column
intervals. Crop to the original chart extent, preserving legend row order.
Unlisted colors are decoys and never add a row. Canvas background is the unique
most frequent color; zero is confined to the chart. A repeated seed is not an
external object. Generated object counts fit the available chart width.

## Native family and causal composition
`count_scope=all` is byte-identical to reference.rkt. `largest_per_color` first
measures occupied-cell areas of each external eight-connected component, groups
records by legend color, and counts every maximum-area object within that color.
Ties count individually, including different shapes with equal occupied area.
The downstream bar counts depend on those measured records. Bounding-box area,
number of foreground pixels, shape uniqueness, four-connectivity, and global
rather than per-color maxima are distinct wrong rules.

## Construction and repaired teaching gap
The setting-neutral sampler supports 2..6 demos and exactly four query inputs.
It varies chart size/location/order, canvas/background, object shape/orientation,
area/shape ties, density, category count, and unlisted distractors. The 30x30 query
has four legend colors and at least fourteen objects distributed across the canvas,
not a padded small example. Queries are independent of demonstration count.
The ordinary generator is standalone; native sampler.py is a byte-identical copy
required by native resource containment and checked by relocation tests.

An actual 64-seed adversarial run found that seeds 46 and 49 could accidentally
present sorted legends in both minimum demonstrations. A numeric-color sorting
rival then fit those demonstrations but disagreed with queries. The frozen seed-46
proof retains exact inputs and both executable rules: six protected evaluations
confirm zero changed demo cells and six changed query cells. It remains replayable
without importing the repaired sampler. The first demonstration now has a
nonmonotonic legend order by construction. Query generation and reference bytes
are unchanged by this repair. Seed-46/49 regression tests were observed failing
before repair and passing afterward.

## Evidence limits and owner steps
The finite audit tests 17 explicit policies, not every imaginable rule. The broad
Python audit is distinguished from protected-Racket original-label, preflight,
boundary, counterexample, and causal checks. Public views expose exactly one
shuffled query and no settings/program/answers/future queries/count hints.
Authoring preflight is not owner qualification or acceptance. Registration,
exact-source native qualification/acceptance and training admission remain owner
steps. No shared canonical authority or approval was changed.
