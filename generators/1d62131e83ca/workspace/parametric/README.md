# Proposed ray-orientation parameter

This directory is a **task-local proposed prototype**. It does not replace the
selected production generator, change `RULE_HASH`, approve a variant, or admit
examples to training.

The prototype keeps the canonical reasoning structure: find the solid blue and
red 2×2 source blocks, choose the relevant outer corner of each block, and paint
a one-cell diagonal ray from that corner to the grid edge. One hidden parameter
is selected once for the complete episode and is shared by every demonstration
and query.

| Parameter | Allowed values | Original/default |
|---|---|---|
| `ray_orientation` | `nw_se`, `ne_sw` | `nw_se` |

- `nw_se` is the exact canonical rule: blue goes up-left from its top-left
  corner; red goes down-right from its bottom-right corner.
- `ne_sw` is the nearby alternative: blue goes up-right from its top-right
  corner; red goes down-left from its bottom-left corner.

The input sampler reuses the selected production generator and retains only the
common support where both settings have nonempty, collision-free rays and their
outputs differ. This stronger paired domain makes the declared rival lawful on
every retained pair. It is a prototype sampling choice, not a production-domain
change.

Episodes expose `demo_count` and `query_count` separately (exact integers 1–8).
The retained evidence uses three demonstrations and four distinct queries. Every
demonstration refutes the other declared setting; every query changes under it.
The exact Racket program is fixed for the whole episode, and all stored answers
are checked through the bundled Racket bridge.

Run from the packet extraction root:

```bash
python3 review.py run python3 \
  generators/1d62131e83ca/workspace/parametric/verify.py \
  --out ../checks/parametric/1d62131e83ca-ray-orientation.json

python3 review.py run python3 -m pytest \
  generators/1d62131e83ca/tests/test_parametric_ray_orientation.py -q

python3 review.py run python3 \
  generators/1d62131e83ca/workspace/parametric/adversarial_check.py \
  --out ../checks/parametric/1d62131e83ca-adversarial.json
```

The verifier writes exact programs under `programs/`, complete private episodes
under `episodes/private/`, answer-masked public challenges under
`episodes/public/`, and a source-bound report under `evidence/manifest.json`.
Public filenames are `challenge-<sha256>.json`, where the digest is computed only
from visible demonstrations and query inputs. Hidden parameters, seeds, Racket,
metadata, and query answers are excluded from both public bytes and identity.

Exact-Racket evidence is bounded to two medium episodes, one per setting. The
separate adversarial checker exercises 24 deterministic episodes across all three
difficulty bands, the 1/1 and 8/8 count boundaries, and public/private identity.
Neither receipt claims all-seed, all-size, or all-rival coverage.
