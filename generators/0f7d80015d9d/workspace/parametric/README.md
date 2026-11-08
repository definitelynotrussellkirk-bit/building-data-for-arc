# Proposed episode-fixed stamp-rule prototype

This directory is deliberately separate from the selected production generator. The canonical setting remains `stamp_relation=opposite, midpoint_side=right`, and `prototype.program_for(DEFAULT_SETTING)` returns the registered canonical Racket program byte-for-byte. The other three settings are proposed authoring variants only; they do not change approval metadata, the canonical rule hash, or production labels.

Two semantic parameters are chosen once per episode:

- `stamp_relation`: put the new cyan cell on the rectangle side **opposite** the original red marker (canonical), or on the **same** side.
- `midpoint_side`: treat a red marker at the rectangle midpoint as part of the **right** side (canonical), or the **left** side.

Object detection, marker movement, rectangle anchoring, palette, and the role of the original red/cyan markers stay invariant. Three demonstrations use strict-left, midpoint, and strict-right red placements; together they uniquely identify all four settings before any query output is considered. The default materialization has four distinct queries and all episode inputs retain a background column on both rectangle sides, making every proposed setting total.

## Focused unit tests

From `WORK/repo`:

```bash
PYTHONPATH=shared/runtime:src python3 -m pytest -q \
  generators/0f7d80015d9d/tests/test_parametric_stamp_rule.py
```

## Exact Racket verification and masked export

From the packet root, after `python3 review.py setup`:

```bash
python3 review.py run python3 \
  generators/0f7d80015d9d/workspace/parametric/verify.py \
  --all-settings \
  --output-dir ../checks/parametric \
  --overwrite
```

A repeat run uses `--overwrite`. Each setting is materialized as a separate episode under an opaque directory named by SHA-256 of the canonical visible challenge bytes. `public.json` contains demonstration inputs/outputs and query inputs only. `private.json` retains the fixed setting, exact rule, query labels, all candidate outputs, source hashes, and demonstration-survivor evidence. `rule.rkt` is the exact selected rule for that episode. The root `manifest.json` records the protected Racket runtime identity and all artifact hashes.

## Retained discovery snapshot

After a successful verifier run, retain a compact source-bound snapshot for the parametric-priority index:

```bash
python3 review.py run python3 \
  generators/0f7d80015d9d/workspace/parametric/retain.py \
  --checks-dir ../checks/parametric \
  --overwrite
```

This copies only opaque public episodes and their exact Racket rules into `examples/` and `racket/`; the setting map remains in a private reviewer summary under `evidence/reviewer-reported/`. `evidence/manifest.json` binds every retained file to the current generator hash and canonical rule hash, marks all variants unapproved, and lets future allocation tooling detect that a current prototype exists without treating it as production.

Verify that source-bound snapshot explicitly (the portable task-test stage intentionally omits retained `evidence/` directories):

```bash
python3 review.py run python3 \
  generators/0f7d80015d9d/workspace/parametric/check_retained.py \
  --out ../checks/parametric-retained-check.json
```

## Limits

This is bounded authoring evidence, not production integration or approval. The verifier covers one deterministic seed for each setting. It checks the four declared parameter alternatives and Python/Racket parity, but not every conceivable human shortcut. Bilateral margin filtering is a prototype-domain constraint needed because the canonical production grammar only guarantees space on the authoritative output side.
