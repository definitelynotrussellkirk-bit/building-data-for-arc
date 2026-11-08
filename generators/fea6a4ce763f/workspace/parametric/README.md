# Connectivity parameter: proposed prototype

This is an isolated **proposed prototype** for `fea6a4ce763f`. It does not
replace the selected `generator.py`, modify the canonical ledger, or approve a
new rule. The canonical/default setting remains the exact program
`(rule! extract-largest)`.

## Parameter

| Parameter | Allowed values | Default | Executed effect |
| --- | --- | --- | --- |
| `connectivity` | `four`, `eight` | `four` | Segment same-colour nonzero objects with 4- or 8-neighbour connectivity, choose the unique largest by cell count, and crop its bounding box. |

The reasoning skeleton is unchanged: **segment objects → compare their sizes →
crop the winner**. Only diagonal adjacency changes. Each generated pair contains
a separate size-6/7 target and two same-colour 2x2 blocks touching at one corner.
Under `four`, the target is largest; under `eight`, the blocks merge into a
size-8 winner. Thus every demonstration distinguishes the two settings. The
setting is chosen once from the episode seed and reused for three demonstrations
and one query.

## Reproduce

From `WORK/` in the extracted packet:

```bash
python3 run_with_racket.py python3 \
  generators/fea6a4ce763f/workspace/parametric/build_prototype.py \
  --out-dir ../checks/parametric/connectivity-v1

python3 run_with_racket.py python3 -m pytest -q \
  generators/fea6a4ce763f/tests/test_parametric_connectivity.py
```

Use a new output directory for each evidence run; the builder refuses to
overwrite evidence.

The retained evidence directory contains redacted `public/` challenges and
private authoring evidence: exact Racket text and hashes for both settings,
complete episodes including query answers, canonical-default execution checks,
matched-input counterfactual outputs, bridge receipts, source hashes, and the
actual command. Public challenges omit the seed, hidden setting, Racket source,
and query answer.

This finite constructor demonstrates a meaningful nearby parameter and correct
episode discipline. It does not establish broad natural-input diversity,
universal correctness, production integration, approval, or training
eligibility.
