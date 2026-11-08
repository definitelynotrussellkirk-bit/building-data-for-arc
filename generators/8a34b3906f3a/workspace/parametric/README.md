# Rotational completion → contacted payload family

The default `completion_style=same_color` is the byte-exact canonical rule:
complete every absent 90-degree copy in color 2.

The nearby `completion_style=contact_payload` setting is deliberately
non-cosmetic:

1. **A — rotational completion:** build the same fourfold-completed red
   intermediate as the canonical rule.
2. **Input-dependent intermediate:** newly completed red touches exactly one
   isolated key among colors 3, 4, and 5.
3. **B — remote payload action:** recolor the contacted key and its distant
   same-color four-cell payload to color 8.

Every input has three equal-frequency key/payload colors, so frequency cannot
select the answer. The minimum two-demo lesson is constructively chosen to
refute fixed colors plus declared position, distance, payload-rank,
wrong-connectivity, and partial-intermediate selectors. Inputs are byte-matched
across settings.

The sampler supports 2–6 demonstrations and exactly four controller-side
queries. Query sizes are 21, 23, 25, and 30. The 30×30 case is a constrained
extension of the exact quotient-center semantics: a lawful 29×29 orbit scene is
embedded at offset `(1,1)`, moving its center to `(15,15)` and keeping all
rotations in bounds. This does not broaden the repaired odd-square base.

Useful commands from the packet outer directory:

```sh
python3 review.py run pytest -q \
  generators/8a34b3906f3a/tests/test_generator_8a34b3906f3a.py \
  generators/8a34b3906f3a/tests/test_parametric_rotation_completion.py \
  generators/8a34b3906f3a/tests/test_adversarial_probe.py

python3 review.py run python3 \
  generators/8a34b3906f3a/workspace/parametric/adversarial_probe.py \
  --seeds 24 --racket-seeds 2 \
  --out ../checks/8a34b3906f3a/adversarial/probe.json

python3 review.py run python3 \
  generators/8a34b3906f3a/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 2 --queries 4 \
  --out generators/8a34b3906f3a/workspace/parametric/evidence
```

These are bounded authoring receipts, not owner acceptance or training
admission.
