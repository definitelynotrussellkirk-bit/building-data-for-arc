# Parametric family for `89dfcff52ee8`

## Episode-fixed parameter

`closure` has two values:

- `rows_only` — the byte-exact canonical rule. For every input row containing
  nonzero markers, paint the inclusive horizontal span from its leftmost to its
  rightmost marker cyan (`8`). A singleton row paints one cyan cell.
- `rows_then_columns` — first perform the same row closure, then for every column
  occupied in that intermediate, paint the inclusive vertical span from its
  topmost to its bottommost intermediate cell cyan.

The alternate is genuinely sequential:

1. **A:** compute horizontal row closures from the input markers.
2. **Intermediate:** the input-dependent set of cells in that row-closure grid.
3. **B:** compute vertical column closures from the intermediate.

Skipping A (column-closing only original markers) or reversing the order changes
protected-Racket outputs on retained 30×30 cases.

## Native contract

`adapter.py` exposes `program(settings)` and
`generate(seed, settings, demos, queries)`. `promotion.json` admits 2–6
independent demonstrations and exactly four controller-side queries. Inputs are
matched across settings; the canonical setting returns the exact selected Racket
source. `prototype.public_turn` exposes all demonstrations and exactly one
query input, with settings, programs, answers and future queries kept private.

## Review tools

`adversarial_probe.py` is the reusable bounded audit. It checks the two-demo
teaching minimum, 32-seed sampler corners, eight shortcut families, crossed
controls, malformed episodes, forged saved certificates, public projection, and
selected protected-Racket episodes plus causal ablations. Run from the library
root through the packet wrapper so the bundled protected Racket is available:

```sh
python3 review.py run python3 \
  generators/89dfcff52ee8/workspace/parametric/adversarial_probe.py \
  --out generators/89dfcff52ee8/workspace/parametric/evidence/current/adversarial.json
```

The finite probe, authoring preflight and witness support owner review. They do
not establish universal uniqueness, owner acceptance, or training admission.
