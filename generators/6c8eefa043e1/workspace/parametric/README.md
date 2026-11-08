# Flood-connectivity parameter: proposed prototype

This is an isolated **proposed prototype** for `6c8eefa043e1`. It does not
replace the selected `generator.py`, edit the canonical ledger, or approve a new
rule. The original/default setting is the exact canonical Racket program.

| Parameter | Allowed values | Default | Executed effect |
| --- | --- | --- | --- |
| `connectivity` | `four`, `eight` | `four` | Process seed markers in row-major order and flood their zero-valued region through orthogonal neighbors or all eight neighbors. |

The reasoning skeleton is preserved: locate colored seeds, remove one marker,
propagate its color through connected background, repeat, and leave gray walls
and seedless components untouched. Every constructed pair has a seedless
satellite that touches one seeded component only at a corner, so the settings
produce different outputs. A second seeded component and a separate unseeded
component retain the original family’s roles. The setting is chosen once from
the episode seed and reused for three demonstrations plus one query.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/6c8eefa043e1/workspace/parametric/build_prototype.py \
  --out-dir ../checks/parametric/connectivity-v1

python3 review.py run python3 -m pytest -q \
  generators/6c8eefa043e1/tests/test_parametric_connectivity.py
```

Use a new output directory for every evidence run; the builder refuses to
overwrite evidence. The retained directory contains redacted public challenges,
exact Racket text and hashes for both settings, complete private episodes,
canonical-default checks, matched-input counterfactual outputs, Racket bridge
receipts, source hashes, and the actual command. Public challenges omit the
hidden setting, seed, Racket source, and query answer.

This bounded constructor demonstrates a meaningful nearby rule parameter and
correct episode discipline. It does not establish broad natural-input diversity,
production integration, universal correctness, approval, or training eligibility.
