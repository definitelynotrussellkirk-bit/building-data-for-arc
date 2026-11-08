# Native payload-policy prototype for 25c140f9307d

This task-local family preserves the approved plate/key input grammar and exact
canonical Racket program. The episode-fixed `payload_policy` has two values:

- `preserve` (default): after matching and rotating each key, stamp its two
  payload colors at their oriented positions.
- `swap`: after the same match and rotation, exchange the two oriented payload
  colors before stamping them.

Both settings therefore require the same causal first stage: a hole selects a
key and its rotation, producing the payload colors and target rim cells consumed
by the second-stage payload policy. Inputs are shared across settings for a given
seed. Supported episodes contain 2–6 demonstrations and exactly four private
queries; one scene is an exact 30×30 input with a substantive 22×22 plate.

From the packet's outer directory:

```sh
python3 review.py run python3 -m pytest \
  generators/25c140f9307d/tests/test_parametric_payload_policy.py -q
python3 review.py run python3 -m arcpuzzles parametric qualify 25c140f9307d \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/25c140f9307d/qualification --summary
```

Qualification and acceptance are separate. This prototype and its reviewer
qualification do not grant owner acceptance or training admission.
