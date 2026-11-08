# Landing-offset parametric prototype

This task-local prototype varies one semantically meaningful rule constant once
per episode:

- `landing_offset = 2` — the canonical rule, placing gray on the penultimate
  route cell.
- `landing_offset = 3` — a proposed variant, placing gray on the antepenultimate
  route cell while keeping the same route traversal, clearing behavior, green
  endpoint, inactive markers, dormant routes, and zero caps.

Every active route in the prototype curriculum has at least three cells, so both
settings are defined. The default materialization is byte-for-byte identical to
the selected canonical Racket source. The alternate materialization changes the
single `(- (length trail) 2)` expression to `(- (length trail) 3)`.

`prototype.py` constructs four calibrated inputs per episode, draws the hidden
setting exactly once from `random.Random(seed).choice((2, 3))`, and delegates all
labels and rival predictions to `label_worker.py` in the bundled Racket runtime.
Public episode files contain three labeled demonstrations and one unlabeled
query input. Parameters, programs, query outputs, rival predictions, runtime
identity, canonical parity, and hashes remain under `private/`.

Run from the review packet root:

```bash
python3 review.py run python3 \
  generators/bf53d21ff9fc/workspace/parametric/prototype.py \
  --out ../checks/parametric/landing-offset-v1 --seeds 0 1
```

The output directory must not already exist. This is authoring evidence only;
it does not change the production generator or approve the offset-3 rule.
