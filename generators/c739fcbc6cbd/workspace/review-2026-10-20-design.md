# c739fcbc6cbd review repair and parameter prototype design

## Intent

Return a source-bound, runnable improvement for the assigned ARC generator rather
than a prose-only review. Preserve the canonical Racket authority and canonical
rule. Repair the measured strict-call defect, add executable semantic evidence
against the strongest canonical-fitting shortcut, make default lessons reliably
teach that distinction, and supply a separate parameterized rule prototype.

## Canonical generator repair

The selected canonical behavior remains unchanged: select the first two nonzero
cells in color-major/row-major order, choose rows versus columns from their
coordinate separations, preserve the blank prefix, and alternate phases with
period `2 * active_distance`.

`generate()` will reject non-literal-integer `seed` values, non-literal-integer
`sample_index` values, and negative `sample_index` values before constructing a
context. This directly addresses the before-battery strict-scalar warnings.

The strongest finite rival is `row_major_first_two`: it selects the first two
nonzero cells in row-major order instead of color-major order, then applies the
same phase rule. It fits all five canonical pairs because they contain exactly
two nonzero cells. A `high_color_decoys` scene will always place a later-color
marker spatially before the intended color-2 marker, so the rival provably
changes the output. The semantic declarations will connect the named canonical
shortcut, witness, and lesson competitor.

For default generation only, even `sample_index` values select the guaranteed
counterexample profile; odd values retain broad seeded profile sampling over all
other declared profiles. Explicit `scene_profile` overrides continue to be
honored exactly and bypass the schedule. With the normal three-demo-plus-query
lesson window, every four consecutive accepted sample indices contain two
counterexamples, so every query rotation leaves at least one counterexample in
the demonstrations. The schedule period is declared as two and can be exhaustively
enumerated by the packet's schedule-census tooling.

## Parametric prototype

A task-local prototype under `workspace/parametric/` varies one rule parameter:
`period_factor` in `{2, 3}`, with canonical/default value `2`. All other object
roles and inference steps remain unchanged. The parameter is chosen once per
episode and reused across three demonstrations and one query.

The prototype emits one exact Racket program per setting, derives all labels by
running that program through the packet's Racket bridge, checks an independent
Python mirror, and requires every retained pair to distinguish the selected
factor from the alternative. Public challenge JSON includes demonstration
answers but omits the query answer and hidden parameter. This remains separate
from selected production authority and makes no approval claim.

## Evidence and testing

New tests live in a new task-local test file; the frozen baseline fixture is not
modified. Tests first reproduce scalar acceptance, canonical shortcut fit,
guaranteed generated counterexamples, rotation-identifiable schedule behavior,
and prototype parameter consistency. Verification then includes task tests, the
full after battery, exhaustive period-2 schedule enumeration, a 100-per-band
rotating lesson census, and the prototype's retained Racket evidence.
