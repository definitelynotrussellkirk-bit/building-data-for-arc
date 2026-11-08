# Rotation-handedness prototype

This source-bound prototype keeps the rotate-and-stamp reasoning pipeline fixed
and varies one episode-private rule parameter: `direction=clockwise` (the exact
canonical program) or `counterclockwise`.  Codes 2 and 6 are unchanged; codes 4
and 9 reverse their quarter-turn interpretation.  Inputs are matched across
settings, contain both discriminating codes, and use separate demonstration and
query streams.  Supported episodes contain 2–6 demonstrations and 1–8 queries;
the default is three demonstrations and four queries, with a substantive 30×30
fourth query.

The finite certificate fits settings using demonstrations only.  `prototype.py`
also provides a protected-Racket evidence exporter whose public files contain
only demonstrations and query inputs; private settings, programs, and answers do
not contribute to the public identifier.

From the packet root:

```bash
python3 review.py run pytest -q generators/8c73e339d80e/tests/test_parametric_handedness.py
python3 review.py run python3 generators/8c73e339d80e/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out generators/8c73e339d80e/workspace/parametric/evidence/current
```

This is retained authoring evidence, not acceptance or training admission.
