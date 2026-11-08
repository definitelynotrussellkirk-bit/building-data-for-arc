# Parametric midpoint selection — `1e26763a6f70`

This family preserves the source task's exact pair analysis and midpoint
construction while varying one episode-fixed selection policy:

- `all_pairs` is the byte-exact canonical Racket rule and marks every eligible
  same-color aligned pair.
- `longest_pairs` derives all eligible pair records and their spans, then marks
  every pair tied for the maximum span.

Inputs are matched across settings.  Demonstrations and queries have independent
stable prefixes (`2..6` demos, `1..4` queries); the fourth query is a genuine
30×30 scene with boundary contacts, both orientations, eight candidate pairs,
and a dense ignored-color distractor.

The causal dependency is pair analysis → the input-dependent list of
`(color, midpoint, orientation, span)` records → selection/painting.  The
longest setting cannot choose its painted midpoints before the span list exists.
`shortest_pairs.rkt` is retained only as a protected-Racket wrong-intermediate
counterfactual for the qualification-bound witness.
