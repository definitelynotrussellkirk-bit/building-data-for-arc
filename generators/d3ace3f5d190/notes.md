# d3ace3f5d190 — current generator decisions

## Base-rule repair

The selected canonical Racket program was preserved byte-for-byte. Its actual
semantics are: for every output position, inspect the input reflected across the
main diagonal; a nonzero reflected value replaces the current value, otherwise
the current value remains. Therefore one-sided marks are copied and conflicting
transposed marks exchange colors. The prior prose incorrectly restricted sources
to below the diagonal, while its ordinary sampler advertised controls it did not
consume and generated only blank mirror destinations, allowing a weaker
copy-into-blanks rule.

Version 2.0.0 repairs those concrete defects. Ordinary scenes contain marks on
both sides and a conflicting transposed pair. `grid_size`/`grid_h`/`grid_w` are
strict square-size controls; incompatible values reject. `palette_kind`,
`anchor_corner`, and `asymmetry_force` now change the generated scene, unknown
keys reject, and the three declared degenerates remain negative self-checks.
Five canonical labeled pairs replay exactly under the executable Python helper.

## Native parametric family

The episode-fixed `axis_rule` parameter has two settings:

- `main` — the exact canonical default.
- `anchor_selected` — find the unique color-8 corner anchor; a northwest or
  southeast anchor selects the main diagonal, while northeast or southwest
  selects the anti diagonal. Apply the same reflected-nonzero-precedence rule
  through that input-selected axis.

This creates the required sequential dependency: **A** locates the anchor,
the intermediate is its coordinates plus the selected axis, and **B** consumes
that axis to choose the reflected coordinate for every output cell. Matched
inputs contain conflicts for both axes, and every two-demo prefix includes both
an anti-selected and main-selected example. Four rivals are executable:
opposite rule, always anti, blank-only copying, and move-only reflection.

The bounded self-review covered 32 seeds, 320 episodes, 2,560 labeled pairs,
every 2–6 demo prefix, four distinct queries, 72 ordinary production probes,
strict-control probes, degenerate rejection, and 30×30 inputs with at least 90
nonzero cells. All 21 focused/staged tests pass. Protected authoring preflight
replayed four jobs and 40 Racket evaluations. The causal witness changes the
selected anti axis to canonical main and changes the final protected output.
Public projection produced 16 one-query views with 24 first-turn invariance
checks and four positive controls.

## Limits

The finite rivals and seeds do not prove universal identifiability. The color-8
corner is a private-family routing marker, not a change to the canonical default.
This return does not claim owner acceptance, catalog approval, production API
promotion, or training admission.
