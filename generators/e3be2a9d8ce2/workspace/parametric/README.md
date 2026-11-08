# Proposed `edge_mode` rule parameter

This directory is an isolated **prototype**. It does not modify the selected
canonical generator, canonical Racket authority, production API, or approval
state.

The parameter is selected once per episode from the deterministic seed:

| Value | Status | Transformation |
|---|---|---|
| `near` | canonical/default | Extend the vertical and horizontal arms to the nearer edges; exact center ties go down/right. |
| `far` | proposed alternative | Extend the same arms to the farther edges; exact center ties go up/left. |

The invariant reasoning is: find the nonzero emitter, preserve its color, and
construct an inclusive vertical-plus-horizontal L-ray through it. The prototype
uses exactly one lawful interior emitter per pair. This retains the original
object role while avoiding unshown overlap precedence, and guarantees every
labelled demonstration distinguishes `near` from `far` before the query.

`near` materializes the exact canonical `program_solution` bytes. The evidence
command writes exact Racket for both settings, executes every label and rival
prediction with the packet's offline Racket bridge, checks Python/Racket parity,
and emits solver-safe public challenges without parameter values, programs, or
query answers.

From the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/e3be2a9d8ce2/workspace/parametric/prototype.py evidence \
  --seed 7319 --out ../checks/parametric/edge-mode-7319

python3 review.py run python3 -m pytest -q \
  generators/e3be2a9d8ce2/tests/test_parametric_edge_mode.py
```

This is finite authoring evidence for two values, not production integration,
training admission, or proof of identifiability against every possible rule.
