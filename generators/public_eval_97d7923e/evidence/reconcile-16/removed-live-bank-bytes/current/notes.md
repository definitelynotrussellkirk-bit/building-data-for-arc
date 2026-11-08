# Current design and implementation

Parent `97d7923e` uses the colored runs touching the top row as rank keys.  A
run of length `k` and color `c` selects the `k`-th longest vertical wire whose
endpoints are both `c` and whose interior is a uniform nonzero different color.
The selected interior is recolored to `c`; other wires are preserved.  Ties use
top row then column order.  The authored general Racket rule reproduces all
three demonstrations and the private public-evaluation gold.

The native parameter is `relay_mode`.  `rank_only` is the exact canonical
program.  `selected_longest` first performs the same rank-coded recoloring,
then identifies the longest *selected* wire and activates the horizontal
`color,9...,9,color` relay for that winning color.  Inputs are matched across
settings and always materialize four distinct queries; the last is a dense
30x30 stress case.

A produces the stage-A grid and selected length for each legend color.  B
consumes those selections to choose the relay color.  Generated scenes
constructively make the longest raw candidate belong to a different color than
the longest rank-selected wire.  The retained protected-Racket counterfactual
uses the raw longest candidates and therefore changes the final output.

This is unapproved authoring work.  Owner registration, exact-source review,
native qualification/acceptance, and any training admission remain pending.
Finite rival checks do not establish universal rule uniqueness.
