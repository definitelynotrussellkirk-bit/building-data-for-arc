# Proposed stamp-transform episodes for `761a24339019`

This task-local prototype is **proposed and unapproved**. It does not change the
selected production generator or its canonical authority.

The episode-fixed parameter is `stamp_transform`:

- `identity` — the exact canonical Racket source, byte for byte.
- `rotate_cw` — rotate every exemplar offset 90° clockwise before stamping it
  at each color-1 target.

The input sampler is independent of the hidden setting. It constructs one
asymmetric mixed color-1/color-3 exemplar, 2–4 widely separated targets, and
color-3-only distractors. Every input is checked to keep both settings in bounds,
collision-free, and prediction-distinct. Demonstrations alone eliminate the
other declared setting. Queries are independently countable; query slot 1 is a
substantive 30×30 boundary case, and four-query episodes contain three more
novel inputs with sides above 20.

From the packet root, create the retained two-setting Racket evidence:

```bash
python3 review.py run python3 \
  generators/761a24339019/workspace/parametric/prototype.py \
  --out generators/761a24339019/workspace/parametric/evidence/current \
  --seeds 0 1 --demos 3 --queries 4
```

Run focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/761a24339019/tests/test_generator_761a24339019.py \
  generators/761a24339019/tests/test_parametric_stamp_transform.py
```

`public_payload()` strips settings, programs, runtime metadata, seeds, and query
answers. `sequential_public_turn(episode, i)` exposes the original demonstrations
plus exactly one query input, with no total-count/future-turn markers. Its first
turn is byte-identical to a one-query episode generated with the same seed and
demonstration count. Public IDs are SHA-256 hashes of `public_challenge_bytes`
only; private files retain all four Racket-derived query labels and teaching
certificates.

The finite tests and retained seeds cover the declared two-setting family; they
do not prove uniqueness against arbitrary programs or approve/admit this family.
