# Native parametric endpoint-cap family

`finish=caps_only` is the exact selected canonical Racket program: each maximal
same-color horizontal nonzero run has its left and right endpoints recolored 1.

`finish=highlight_largest_cap_component` adds a real sequential dependency.
Step A performs the canonical cap pass. Its input-dependent intermediate is the
set of four-connected color-1 components created when endpoints from differently
colored runs become the same color. Step B selects the unique component with the
most occupied cells and recolors exactly that component 8. A larger-bounding-box
counterexample is present in every scene, so bbox area cannot replace occupied
area.

Inputs are matched across settings, deterministic and prefix-stable for 2–6
demonstrations and 1–4 queries. Query sizes are independently shuffled and the
four-query bank includes a substantive 30×30 scene with foreground content
spread to every border region. `public_turn()` exposes one current query input
without settings, programs, answers, future inputs or a total-query hint.

`audit.py` performs the bounded protected-Racket teaching/parity audit. Its
finite rivals and seeds are not a universal uniqueness or learning claim.
