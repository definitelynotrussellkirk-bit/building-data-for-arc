# Task-local review tools — 8dd23f285c61

`reference_probe.py` is an independent geometry oracle and repeatable
input-distribution audit. It does not import generator helpers. The optional
`--racket` mode executes the unchanged canonical authority through
`Catalog.apply`; it never substitutes the Python mirror for authority evidence.

From the repository root in an executable checkout:

```bash
PYTHONPATH=src:shared/runtime python3 -B generators/8dd23f285c61/workspace/reference_probe.py \
  --count 256 --racket --out /tmp/8dd23f285c61-audit.json
```

The report binds the selected generator hash, checks every canonical pair,
discovers and executes the generator's declared shortcuts/competitors, measures
exact axis coverage in all four bands, verifies that each ordinary draw contains
the declared tiny-wall shortcut counterexample, and checks every cyclic lesson
start under the documented `EXAMPLES_NEEDED`-demos-plus-next-query policy. The
optional Racket pass compares canonical, hand-written, and generated inputs to
the public canonical authority.
