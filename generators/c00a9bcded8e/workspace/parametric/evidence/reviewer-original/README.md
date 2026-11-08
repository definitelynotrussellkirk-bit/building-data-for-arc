# Proposed parametric extension: horizontal read direction

This directory is an **isolated prototype**, not a selected production rule.
It preserves the canonical task's rectangle detection, spatial row grouping,
noise distribution, and `N × 3` output shape. One episode-level parameter changes
only the order used to read each row:

- `left_to_right` — canonical/default; exact selected canonical Racket source,
  normalized hash `4732b1c1a64d`.
- `right_to_left` — proposed alternative; reverses the two within-row sort sites,
  normalized hash `ad40d391ac19`.

The setting is chosen once per episode. Each episode contains three demonstrations
and one query built from identical inputs for both settings. Fixtures force the
selected generator's five-target-color `column_repeat` signature so every
training pair distinguishes the two rules without changing the original object
roles or geometry.

## Reproduce

From the packet root:

```bash
python3 review.py run python3 \
  generators/c00a9bcded8e/workspace/parametric/prototype.py \
  --seed 20261023 \
  --out ../checks/parametric/horizontal-read-direction-report.json \
  --examples-dir generators/c00a9bcded8e/workspace/parametric/examples \
  --rules-dir generators/c00a9bcded8e/workspace/parametric/rules
```

The retained report executes both Racket programs on all four pairs per setting
and compares them with an independent Python implementation. Public challenge
files omit the hidden parameter, Racket source, metadata, and query answer.

## Evidence and limits

Final evidence is in
`checks/parametric/horizontal-read-direction-report.json`, bound to generator
SHA-256 `1b5e71b5ced5a6b441a44456d13ed93602561cb8017931f44ef0dcb0c7f9e097`.
Both settings passed 4/4 Racket/Python comparisons (8/8 total), and every one of
the six demonstrations refutes the other setting.

This is one seed and a finite two-setting family. It does not establish universal
rule induction, approve the alternative for training, or modify the canonical
execution path. The forced color-pattern signature is an authoring device for
identifiability, not a new semantic requirement of the Racket rule.
