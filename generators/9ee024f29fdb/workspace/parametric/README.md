# Period-and-paint parametric prototype

The proposed episode-fixed family preserves the canonical lattice reasoning:
zero-based rows and columns divisible by `period` are cleared; outside that
lattice cyan `8` is cleared and every other value is repainted `paint_color`.

- `period ∈ {3,4,5}`
- `paint_color ∈ {2,4}`
- default `(4,2)` is the exact canonical Racket program, byte for byte

`adapter.py` plus `promotion.json` provide the native promotion contract. The
adapter accepts 2–6 demonstrations and 1–4 queries. Inputs use a separate RNG
stream from the setting, every example contains constructive witnesses for all
six setting pairs, and the fourth query is a substantive 30×30 canvas. Query
prefixes are stable, so one-query use has exactly the same first query as the
four-query sequential-reveal use.

`prototype.py` materializes six complete Racket-backed episodes with three demos
and four queries each. Public files contain only visible demos and query inputs,
are written as exact `reviewer_support.public_challenge_bytes`, and use packet-conformant
`challenge-<full-SHA-256>.json` names derived from those exact bytes. Private files retain settings, exact
programs, labels, hashes and demonstration-only finite-rival checks.

```bash
python3 review.py run python3 \
  generators/9ee024f29fdb/workspace/parametric/prototype.py \
  --base-seed 20261019 \
  --out ../checks/parametric/9ee024f29fdb-period-paint-v2

python3 review.py run python3 -m pytest -q \
  generators/9ee024f29fdb/tests/test_parametric_period_paint.py \
  --basetemp /tmp/9ee024f-parametric-tests
```

This remains a bounded proposed prototype, not acceptance or training admission.
