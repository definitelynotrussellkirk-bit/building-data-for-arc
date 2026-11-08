# Proposed `bridge_scope` rule parameter

This task-local prototype preserves the original family’s exact-mask key
identification, key recoloring, lattice geometry, and aligned-pair reasoning.
It changes only which aligned key pairs create color-7 bridges:

- `all_pairs` — canonical/default: every horizontally or vertically aligned key
  pair contributes its intervening non-key tiles.
- `seed_only` — proposed alternative: only pairs containing the distinguished
  color-8 seed contribute bridges.

The value is selected once from the episode seed and reused for every
training/query pair. The canonical input sampler already guarantees a bridge
created by a non-seed pair, so each retained demonstration distinguishes the two
settings. This is proposed authoring evidence only; it does not modify the
selected production rule or approval hash.

From the outer packet directory, materialize both complete episodes, exact
Racket programs, public challenges, hashes, and parity evidence with:

```bash
python3 review.py run python3 generators/79a30e61d332/workspace/parametric/prototype.py \
  --out ../checks/parametric
```

The public challenge files contain demonstration answers but omit the hidden
parameter, Racket text, and query answers. `evidence.json` records the two seeds,
source hashes, exact program hashes, Racket verification, and per-demonstration
output differences against the other parameter setting.
