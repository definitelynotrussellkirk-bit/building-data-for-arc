# Yellow-turn parametric prototype

This proposed family preserves the cyan square, gray blockers, canonical red
outward diagonals, alternating yellow staircase state, and all gray stopping
branches. One episode-fixed parameter changes only which adjacent direction the
yellow ray takes around each square corner:

- `clockwise` — exact canonical Racket source, byte for byte.
- `counterclockwise` — the complementary tangent staircase directions.

The native `adapter.py`/`promotion.json` contract supports 2–6 demonstrations
and 1–4 queries. Inputs are constructed independently of the private turn and
contain open controls, direct and paired red blockers, yellow start/intermediate/
next-diagonal blockers for both turn systems, boundary gray contacts, and decoys.
The separate prototype grammar naturally extends beyond the production 16..23
range to substantive 24×24 and 30×30 stress queries. Query prefixes are stable.

`prototype.py` executes every retained label under bundled Racket, compares an
independent Python mirror, checks the finite rival from demonstrations only, and
writes exact `reviewer_support.public_challenge_bytes` under packet-conformant
`challenge-<full-visible-byte-SHA-256>.json` names, with settings/programs/query labels private.

```bash
python3 review.py run python3 \
  generators/fbf36c193fa6/workspace/parametric/prototype.py \
  --base-seed 20261024 \
  --out ../checks/parametric/fbf36c193fa6-yellow-turn-v1/gallery

python3 review.py run python3 -m pytest -q \
  generators/fbf36c193fa6/tests/test_parametric_yellow_turn.py \
  --basetemp /tmp/fbf36c-parametric-tests
```

This is proposed bounded evidence, not acceptance or training admission.
