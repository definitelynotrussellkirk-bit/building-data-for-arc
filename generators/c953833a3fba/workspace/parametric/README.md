# Manhattan shell-radius prototype

This prototype keeps the canonical center-set inference and exact minimum-
Manhattan-distance shell operation, while varying one episode-private rule
parameter: `radius=2` (the byte-exact canonical program) or `radius=3`.  Center
colors remain irrelevant and output is always cyan on a fresh black canvas.

Inputs are matched across settings, contain cyan and non-cyan centers, use
independent demonstration/query streams, and support 2–6 demonstrations plus
1–8 queries.  The fourth query is a 30×30 four-center stress case spanning more
than twenty rows and columns.  Demonstrations alone must leave exactly the
selected radius in the finite setting family.

From the packet root:

```bash
python3 review.py run pytest -q generators/c953833a3fba/tests/test_parametric_radius.py
python3 review.py run python3 generators/c953833a3fba/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out generators/c953833a3fba/workspace/parametric/evidence/current
```

The exporter replays every selected label through protected Racket and separates
hash-named public challenges from private settings, programs, and query answers.
This is authoring evidence, not acceptance or training admission.
