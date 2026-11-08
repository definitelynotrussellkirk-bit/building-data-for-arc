# Working notes: 9c5bdbcdcd50

## Current parametric design

`workspace/parametric/` adds the episode-fixed `anchor=frame|largest` family.
`frame` preserves the exact current canonical Racket source; the production
generator is unchanged. `largest` binds the unique largest divider-bounded
rectangle, then uses its matrix position to classify and color surrounding
regions. This input-derived coordinate is necessary for the later choice of
quadrant/axis colors. It is not a claim of iterative updated-state reasoning.

The separate grammar admits 3..6 bands per axis, widths 1..6 with unique
maxima, complete internal dividers, and boundary as well as interior pivots.
It supports substantive 6x6 through 30x30 grids; ties are outside this grammar.
Largest area factorizes into tallest row and widest column, an equivalent
valid algorithm rather than a shortcut to reject.

Two constructive demos are the minimum: an off-center interior pivot on a
five-by-five region lattice, then a different boundary pivot on four-by-four.
A central three-by-three lattice alone would not distinguish the settings.
The initial two-demo schedule also allowed a mirrored-axis shortcut: derive
the selected column from the row instead of measuring column widths. A live
protected-Racket counterexample confirmed that rival fit both demos but changed
query zero. The second demo now uses pivot `(0,0)`, breaking both row-derived
and column-derived versions without adding a demo; the regression is retained.
The default uses three demos; 2..6 are supported independently from 1..4
queries. Inputs are matched across settings and stable when counts increase.
Four-query canvases are 6x6, 13x19, 24x27 and 30x30; all inputs are distinct by
construction. Task-local `probe.py` retains protected-Racket labels, bounded
demonstration-only rival evidence, public projections and causal cases.

Next owner action is exact-source native qualification and acceptance after
intake. Reviewer-ready evidence does not grant acceptance or training admission.
The earlier `needs_triage` audit remains unresolved; this prototype does not
clear historical findings or recheck the unchanged canonical sampler.
Its old exact-program hash is historical; the current canonical program hash
is `4b84d3d083f65dd1308ec1941060c395f565103bf41b79a9713164eadd8942e7`.
