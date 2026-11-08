# Task-local tools — 6737eb62cf42

`reference_probe.py` is a repeatable independent check for the crop generator. It imports the actual declarations rather than copying rival names, verifies every canonical shortcut on all usable canonical labels, exhausts the 480-member public override product, checks all 80 cyclic schedule windows and 320 query rotations across the four difficulty settings, and writes the exact singleton-boundary witness used for an authoritative Racket application.

From `repo/`:

```bash
PYTHONPATH=shared/runtime:src python3 -B generators/6737eb62cf42/workspace/reference_probe.py \
  --out ../checks/reference-probe-final.json \
  --witness-input ../checks/shortcut-witness-input.json
```

Then, from the packet root with the supported wrapper:

```bash
python3 review.py run python3 -m arcpuzzles apply 6737eb62cf42 \
  --input ../checks/shortcut-witness-input.json \
  --out ../checks/shortcut-witness-racket.json
```

The Python crop oracle is deliberately independent of `generator.rule_mirror`; it is supplementary evidence only. The selected Racket program remains the label authority. Finite rival checks do not prove identifiability against undeclared programs.
