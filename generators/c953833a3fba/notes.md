# Working notes: c953833a3fba

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 radius proposal and canonical generator repairs

Built `workspace/parametric/` around `radius=2|3`. Radius 2 is the byte-exact
canonical minimum-Manhattan-distance shell program; radius 3 changes only the
executed shell distance while preserving center-set inference, fresh-canvas
output, and fixed cyan labels. Inputs are matched across settings, deliberately
mix cyan and non-cyan centers, use independent demo/query streams, support 2–6
demos and 1–8 queries, and keep query prefixes stable. The fourth ordinary query
is a four-center 30x30 case spanning more than twenty rows and columns.

Two source defects encountered during this work were repaired in `generator.py`.
`CANONICAL_SHORTCUTS` no longer incorrectly lists semantic rivals that do not fit
the canonical rule, and the color-generalization slot now actually samples a
cyan input center when multiple centers are present. Minimal regressions retain
both fixes. Focused tests and protected-Racket evidence cover the two radii,
count boundaries, matched inputs, public/private separation, center-color
invariance, rejection paths, and the 30x30 case. The bounded adversarial pass
generated 32 episodes over four count corners, four seeds, and both settings.

Native qualification was attempted but correctly refused before execution
because this repaired production generator is not yet approved on its current
source/rule. The next step is owner review/approval of the repaired generator,
then rerun the existing `parametric qualify` command. No approval state was
changed or bypassed. The radius family remains a proposed variant and is not
accepted or admitted to training.
