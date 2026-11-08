# Object parsing × halo basis family — proposed

This native adapter keeps the task's two-stage mechanism intact:

1. parse each color-preserving nonzero object and measure its bounding box;
2. derive a halo radius, paint the blue downward stem, then paint the clipped
   green halo while preserving original maroon cells.

It exposes two nearby choices that can be taught by ordinary demonstrations:

| Parameter | Values | Canonical default |
|---|---|---|
| `connectivity` | exact integers `4`, `8` | `8` |
| `border_basis` | `min_side`, `max_side` | `max_side` |

The default returns the selected canonical Racket source byte-for-byte. The
other three programs change exactly one or both of `(objects-8 g bg)` and
`(max rh rw)`. No production generator, authority, or approval is changed.

## Sampler and lesson contract

`generate(seed, settings, demos, queries)` accepts 2–6 demonstrations and
exactly four queries. Inputs are sampled before and independently of settings;
the same seed and counts therefore produce byte-identical inputs for all four
programs. Earlier demonstrations and all queries remain stable when the demo
count grows.

Every ordinary demonstration includes:

- same-color lobes touching only diagonally, separating 4- from 8-connectivity;
- a non-square object, separating max-side from min-side halo width;
- a non-maroon object, an irregular object, and a maroon singleton, rejecting
  maroon-only, solid-rectangle-only, and singleton-omission shortcuts.

The four queries are an ordinary 10×10 maroon anchor, a 16×18 transfer scene,
a 21×14 clipped boundary scene, and a substantive 30×30 multi-object stress
scene. Query answers are never read by the lesson certificate. `visible_turn`,
`visible_turn_bytes`, and `visible_turn_id` use the shared public-challenge helper
to expose one controller-selected query only; the payload has no turn index,
total-count field, future input, private setting, program, seed, or query label.
The first-turn bytes therefore match the same query projected in isolation.

The Python mirror is an audit aid. Promotion qualification executes every
label with the same-checkout protected Racket backend and verifies that the
chosen setting is the sole declared program surviving the demonstrations.
The finite certificate does not claim exhaustive induction over every possible
rule.

## Verification from the packet root

```bash
source WORK/.venv/bin/activate
python review.py task-tests 067449d7a3b3 --phase after \
  --out ../checks/067449d7a3b3-parametric-tests
python review.py run python3 -m arcpuzzles parametric manifest 067449d7a3b3
python review.py run python3 -m arcpuzzles parametric qualify 067449d7a3b3 \
  --out ../checks/067449d7a3b3/qualification --summary
```

The family remains proposed and `training_admitted: false`; owner acceptance is
still a separate explicit action.
