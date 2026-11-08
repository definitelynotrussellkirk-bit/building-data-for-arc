# 20014c9d3729 native parametric family

`selection_policy=per_color_largest` is the exact selected canonical Racket
source. `selection_policy=min_winner_threshold` first finds the unique largest
object of every color, relays the smallest winner size, then keeps every object
whose size meets that input-derived threshold.

Inputs are identical across settings. The sampler supports 2–6 demonstrations
and 1–4 queries with stable prefixes. Every ordinary scene contains a loser at
the relayed threshold, so the two rules differ; the first two demonstrations
also vary the threshold to refute a fixed-size shortcut. The fourth query is a
substantive boundary-spanning 30×30 scene with 16 components and 46 colored
cells.

Sequential dependency: A selects per-color winners; the intermediate is their
size map and minimum; B uses that minimum to filter all components. The retained
counterfactual relays the maximum winner size instead.
