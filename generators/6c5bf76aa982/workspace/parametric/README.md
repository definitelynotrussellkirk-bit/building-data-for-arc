# Signal-selected border-count native parametric family

**Status: reviewer-qualified source candidate; owner acceptance pending.** The
production generator and canonical authority are unchanged. The default setting
returns the selected canonical Racket source byte-for-byte. Neither this source
candidate nor its generated episodes are admitted to training.

## Rule parameter

| `border_policy` | Meaning |
| --- | --- |
| `exactly_one` | Canonical: recolor each orange component green exactly when it touches one distinct canvas border. |
| `signal_target` | Count the cells in the unique cyan signal and recolor each orange component whose distinct-border count equals that signal-derived target. |

The input sampler is independent of the private setting. Every scene contains
orange components touching exactly zero, one, two, and three distinct borders,
and a connected cyan signal of size two or three. It supports 2–6 demonstrations
and exactly four independently generated, prefix-stable queries. Query shapes
are 15×17, 20×22, 25×27, and 30×30. The 30×30 scene has substantial content and
nonzero contact on every canvas boundary. All pair inputs are distinct.

## Sequential dependency

- **Step A:** count the cyan signal cells.
- **Intermediate:** the target distinct-border count plus the orange-component touch inventory.
- **Step B:** recolor exactly the orange components whose touch count equals the target.
- **Why B depends on A:** the selected orange components cannot be known until the signal-derived target is measured.

The retained protected-Racket witness replaces the measured target with a wrong
border count on the same qualified input and changes the final output.

## Reproduce

From the packet’s outer directory:

```bash
python3 review.py task-tests 6c5bf76aa982 --phase after \
  --out ../checks/6c5bf76aa982-tests
python3 review.py run python3 generators/6c5bf76aa982/workspace/parametric/audit_lessons.py \
  --seeds 64 \
  --out generators/6c5bf76aa982/workspace/parametric/evidence/self_audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 6c5bf76aa982 \
  --out ../checks/6c5bf76aa982/qualification --summary
```

The finite self-audit checks both declared settings, nine named shortcut rules,
matched inputs, demonstration-count boundaries, query-prefix stability, public
projection, and exact 30×30 coverage. It is not a universal uniqueness or
model-learning proof.
