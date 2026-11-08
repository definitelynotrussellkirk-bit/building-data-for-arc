# Native closure-order family

This directory is the task-local, source-bound parametric implementation for `8e52225f35b8`.

- `canonical.rkt` — exact canonical bytes, no trailing newline.
- `prototype.py` — strict Python reference, sampler, certificate, public-turn projection, analysis, and protected-Racket helper.
- `adapter.py` — minimal native qualification adapter.
- `promotion.json` — finite settings/count contract.
- `adversarial_probe.py` — reusable bounded self-review across fresh seeds, semantic rivals, count corners, privacy, malformed contracts, 30×30 spread, and protected Racket.
- `evidence/manifest.json` — current source inventory; regenerate after changing any `.py`, `.rkt`, or `.json` source here.

From the packet outer directory:

```bash
python3 review.py run pytest -q generators/8e52225f35b8/tests/test_parametric_closure_order.py
python3 review.py run python3 generators/8e52225f35b8/workspace/parametric/adversarial_probe.py \
  --out generators/8e52225f35b8/workspace/parametric/evidence/adversarial_probe.json
python3 review.py run python3 -m arcpuzzles parametric manifest 8e52225f35b8 \
  --evidence generators/8e52225f35b8/workspace/parametric/evidence \
  --include generators/8e52225f35b8/tests \
  --reported-checks 'replace with checks actually run'
python3 review.py run python3 -m arcpuzzles.review_base_preflight 8e52225f35b8 \
  --demos 2 --out ../checks/8e52225f35b8/qualification
```

`review_base_preflight --out` expects a path that does not already exist. Any source edit after preflight invalidates the qualification, witness, and export receipts; rebuild them in that order.
