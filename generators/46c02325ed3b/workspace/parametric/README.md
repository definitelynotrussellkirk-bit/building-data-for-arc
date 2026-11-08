# 46c02325ed3b spread-policy prototype

**Prototype evidence only.** The canonical generator, selected Racket
authority, approval state, and training admission remain unchanged.

`spread_policy` is fixed for an episode. `both` is the exact canonical program:
water spreads along both directions of a blocking cyan wall. The alternate
`right_hand_only` keeps only the geometric right-hand branch relative to inward
gravity. Every sampled input has paired reachable holes, so the same grids are
valid under both settings while their labels expose the setting.

The four retained query streams rotate through top, bottom, left, and right
sources and use 10×10, 14×17, 18×18, and substantive 30×30 layouts. The 30×30
case contains five full wall lines rather than padding a small puzzle.

From the packet directory:

```bash
python3 review.py run python3 -m pytest \
  generators/46c02325ed3b/tests/test_parametric_spread_policy.py -q
python3 review.py run python3 \
  generators/46c02325ed3b/workspace/parametric/prototype.py build \
  --seed 17 --demos 3 --queries 4 \
  --out generators/46c02325ed3b/workspace/parametric/evidence/current
```

The atomic writer hashes exact public bytes containing only demonstrations and
query inputs. Private settings, programs, answers, demo-only certificates,
source bindings, and protected-Racket identity are separate. Verification
replays both programs against every pair and rejects inventory, runtime, label,
and identity tampering.
