# Native parametric corner-ring family

This task-local family preserves the canonical corner-ring reasoning while
adding two episode-fixed rule parameters:

- `ring_step=2|4`: adjacent odd rings (canonical) or rings separated by one
  blank cell on every side.
- `corners=all|diagonal`: all four corner Ls (canonical) or only the
  top-left/bottom-right pair.

The default `(2, all)` Racket program is byte-identical to the canonical rule.
Inputs are independent of the hidden setting, and the four query inputs are
stable when the demonstration count changes from 2 through 6. Every episode has
exactly four distinct queries. Query four is a substantive 30×30 stress case:
six lawful glyphs retain their measured geometry while being spread across all
four canvas boundaries.

## Execution boundary

`prototype.py` is the rich authoring/audit interface. It executes labels and all
finite-family rival predictions through protected Racket, then cross-checks them
with the independent Python transform.

`adapter.py` is the thin native promotion interface. Its `generate` method emits
deterministic Python claim labels without starting an embedded Racket process.
The native qualification worker independently executes every exact
`program_solution` through protected Racket and rejects any claim mismatch. This
separation avoids nested interpreter lifetimes while retaining Racket as the
qualification authority.

## Required causal dependency

1. Measure each color's maximum bounding-box dimension and longest corner arm.
2. Carry `{color, max_dim, arm}`, `has_center`, and the resulting ring schedule.
3. Allocate colors to fitting rings using `max_dim`, then paint corner Ls using
   the measured `arm`.

The retained protected-Racket witness replaces every measured arm with `1` and
changes the final grid, demonstrating that rendering consumes the measured
intermediate rather than merely following code order.

## Verification

From the packet extraction root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/5a01897eb8be/tests/test_parametric_native_adapter.py
python3 review.py run python3 -m pytest -q \
  generators/5a01897eb8be/tests/test_parametric_corner_rings.py
python3 review.py run python3 -m arcpuzzles parametric qualify 5a01897eb8be \
  --out ../checks/5a01897eb8be/qualification --summary
```

The promotion contract is `promotion.json`; the current source inventory is
`evidence/manifest.json`. Qualification and causal replay receipts are retained
under `WORK/checks/5a01897eb8be/`.

## Scope

This is reviewer-ready native promotion evidence, not owner acceptance or
training admission. Qualification covers the four declared settings at finite
fresh seeds and proves neither universal identifiability nor measured training
gain. The production generator remains unchanged and keeps its 13–24 by 17–24
distribution; only the separate parametric query stream adds the lawful 30×30
stress profile.
