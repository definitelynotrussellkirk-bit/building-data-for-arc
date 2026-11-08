# f4dc936dfcbb — intersect row spans and column spans

Implementation version: `3.0.0`. Canonical rule hash: `b804c88a8a55`.

The input is an 8–18 by 9–20 zero-background grid. One to three rows each
contain exactly two red (`2`) endpoints, defining inclusive horizontal spans.
One to three columns each contain exactly two green (`3`) endpoints, defining
inclusive vertical spans. One ignored non-rule color appears in one to four
distractor cells.

The output is a **fresh zero grid** of the same dimensions. For every selected
row and selected column, place cyan (`8`) at their coordinate only when the
column lies inside that row's red span **and** the row lies inside that column's
green span. Input endpoints and distractors do not survive into the output.

The default sampler uses two or three row and column spans and constructs both
one-gate negative cases: a pair that passes only horizontal containment and a
pair that passes only vertical containment. This refutes `horizontal_only`,
`vertical_only`, and `all_span_pairs` shortcuts in every ordinary draw. Exact
overrides remain available for one to three spans, dimensions, and distractor
count. A canonical-profile branch covers all five canonical shape/palette
profiles in every difficulty band, while a broad branch covers the declared
dimension ranges.

`strict_canonical_like`, `observe_overrides`, semantic witnesses/rivals, and 34
task-local tests form the executable contract. The selected Racket source is
byte-synchronized to the canonical program; its behavior is unchanged.
