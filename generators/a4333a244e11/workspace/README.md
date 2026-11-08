# Reviewer workspace

`reference_probe.py` is an independent oracle and reproducible audit utility for
this task. It deliberately reimplements the two-seed Manhattan rule and five
plausible rivals instead of importing the production generator's rule helper.
It resolves canonical data through `reviewer_support.find_root`, so it works in
the source tree and relocated task-test runtimes.

From the extracted packet root, run:

```bash
python3 run_with_racket.py python3 \
  generators/a4333a244e11/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/reference-probe-final-v2.json
```

The report records final generator/rule hashes, canonical parity, deterministic
sampling, per-band unique-input counts and axis support, disagreements for each
rival, and optional parity against the selected real Racket authority. Racket
failure is reported explicitly; the tool never silently substitutes its Python
oracle as label authority.

The selected implementation is `../generator.py`; workspace tools are never
automatically selected for generation.
