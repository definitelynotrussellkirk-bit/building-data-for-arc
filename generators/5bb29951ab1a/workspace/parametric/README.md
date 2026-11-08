# Threshold-rule prototype for `5bb29951ab1a`

Status: **proposed prototype**, not part of the selected canonical execution path.

The canonical task absorbs a sparse-color dot when at least two of its four
orthogonal neighbors have the modal nonzero rectangle color. This prototype
keeps the same role inference, neighborhood, recoloring, and background behavior
while choosing one episode-wide parameter:

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `orthogonal_neighbor_threshold` | `1`, `2`, `3` | `2` |

Each retained pair contains sparse dots with support degrees 0, 1, 2, and at
least one of 3 or 4. Thus every demonstration shows both branches for every
setting and separates the chosen threshold from the other two allowed settings.
The threshold is chosen once from the episode seed and reused for every train and
test pair.

## Files

- `threshold_prototype.py` builds episodes, emits exact Racket, mirrors the rule
  independently in Python, strips public challenges, and executes arbitrary
  prototype programs through the packet's pinned Racket runtime.
- `materialize.py` creates one complete episode per threshold, verifies every
  label with Racket, records source/program/episode hashes and rival witnesses,
  and writes answer-free public challenges under `examples/`.
- `examples/threshold-*-challenge.json` contain demonstrations and query inputs
  only. They omit threshold metadata, executable source, and query outputs.

## Reproduce

From the extracted packet root:

```bash
python3 review.py setup
python3 review.py run python3 \
  generators/5bb29951ab1a/workspace/parametric/materialize.py \
  --out-dir ../checks/parametric/threshold-v1 \
  --examples-dir generators/5bb29951ab1a/workspace/parametric/examples \
  --seed-base 9400

python3 review.py run python3 -m pytest -q \
  generators/5bb29951ab1a/tests/test_parametric_threshold.py
```

The first command writes full private episodes, exact Racket text, hashes,
adjacency histograms, rival-disagreement indices, and a manifest under
`WORK/checks/parametric/threshold-v1/`.

## Limits

This is bounded evidence for three deterministic episodes. It does not change
or approve the production generator, prove identifiability against arbitrary
unlisted programs, or cover every lawful grid. Frequency-role inference retains
the canonical assumptions of exactly two nonzero colors and a strictly more
frequent rectangle color.
