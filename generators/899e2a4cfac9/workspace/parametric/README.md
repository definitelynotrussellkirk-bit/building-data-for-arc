# Border-signal rank parametric family

The default `retention=all_interior` is the exact selected canonical Racket
program: erase every same-color four-connected object that touches any grid edge
and preserve every fully interior object. The alternative
`retention=signal_rank` keeps the same component and border reasoning, then uses
the unique blue border signal as an input-derived selector:

1. **A:** find the unique blue border component and count its cells.
2. **Intermediate:** that count is a one-based rank.
3. **B:** enumerate fully interior components in row-major discovery order and
   retain only the component at that rank.

B cannot choose an answer object before A produces the rank. Inputs are identical
between settings for the same seed/count request. The first two demonstrations
use different ranks and layouts and reject the declared alternate plus fixed
rank, extrema, column-major, reversed-order, target-size, and border-cells-only
shortcuts. The grammar also includes same-color diagonal border/interior objects,
repeated colors across erased/retained roles, inward border tails, all four edges,
and distinct object sizes and positions.

The adapter supports 2–6 demonstrations and 1–4 independently requested queries.
Query prefixes are stable. The four query profiles are 15×17, 19×21, 24×27, and
a substantive 30×30 scene with eight spread interior objects. Settings, exact
programs, query answers, seeds, future queries, and total-query hints remain
private; public projection exposes demonstrations and one query input at a time.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/899e2a4cfac9/tests/test_parametric_signal_rank.py
python3 review.py run python3 \
  generators/899e2a4cfac9/workspace/parametric/audit_lessons.py \
  --out ../checks/899e2a4cfac9/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric manifest 899e2a4cfac9 \
  --evidence generators/899e2a4cfac9/workspace/parametric/evidence/current \
  --include generators/899e2a4cfac9/tests/test_parametric_signal_rank.py \
  --reported-checks 'focused pytest; bounded finite-rival lesson audit'
python3 review.py run python3 -m arcpuzzles parametric qualify 899e2a4cfac9 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/899e2a4cfac9/qualification --summary
```

Python outputs are sampler claims. Native qualification re-executes every label
through protected Racket. Reviewer readiness grants neither owner acceptance nor
training admission.
