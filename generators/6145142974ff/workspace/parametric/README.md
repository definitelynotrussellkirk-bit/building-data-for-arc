# Native parametric family for `6145142974ff`

The default `finish=canonical` returns the selected canonical program byte-for-byte.
The alternate `finish=bridge_matches` is sequential:

1. **Stage A:** identify exact translation-only color-3 copies of the color-1 template and paint them with the strict-majority marker color on a blank grid.
2. **Intermediate:** the same-size grid containing only those selected components.
3. **Stage B:** rediscover the intermediate components in reading order and connect consecutive components using closest endpoints and a deterministic horizontal-then-vertical Manhattan bridge.

`all_green_bridge.rkt` is a bounded wrong-intermediate counterfactual: it feeds every green component into the same Stage-B bridge operation. It is evidence tooling, not an admitted setting.

## Focused checks

From the packet root:

```bash
python3 review.py task-tests 6145142974ff --phase after --out ../checks/6145142974ff-tests
python3 review.py run python3 generators/6145142974ff/workspace/parametric/audit.py \
  --out generators/6145142974ff/workspace/parametric/evidence/current/structural-audit.json \
  --public-dir generators/6145142974ff/workspace/parametric/evidence/current/public \
  --seed-count 32 --seed 0 --demos 3
python3 review.py run python3 generators/6145142974ff/workspace/parametric/racket_audit.py \
  --out generators/6145142974ff/workspace/parametric/evidence/current/racket-audit.json
```

## Native qualification

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 6145142974ff \
  --evidence generators/6145142974ff/workspace/parametric/evidence/current \
  --include generators/6145142974ff/tests/test_parametric_bridge.py \
  --include generators/6145142974ff/tests/test_parametric_audit.py \
  --reported-checks 'Describe only checks actually run'
python3 review.py run python3 -m arcpuzzles parametric qualify 6145142974ff \
  --out ../checks/6145142974ff/qualification --summary
```

The adapter supports 2–6 demonstrations and 1–4 queries. Inputs are sampled independently of the private setting; the fourth query is a 30×30 scene with six exact matches and five equal-area distractors. Public files contain the demonstrations plus exactly one masked query and are named only by SHA-256 of their visible bytes.
