# ba5056d6102e review workspace

The selected implementation is `../generator.py`. These source-bound tools are
retained so a later reviewer can reproduce the claims without copying the
generator's own oracle into the test.

## `reference_probe.py`

Loads the canonical row, splits panels, computes an independent
Boolean-intersection output, counts occupancy states, and observes ordered panel
colors. It can optionally load a candidate generator path through
`GENERATOR_UNDER_TEST`.

Run every task-local regression, from `repo/`:

```bash
env PYTHONPATH=shared/runtime python3 -m pytest -q \
  generators/ba5056d6102e/tests
```

To test another candidate source:

```bash
env PYTHONPATH=shared/runtime \
  GENERATOR_UNDER_TEST=/absolute/path/to/generator.py \
  python3 -m pytest -q generators/ba5056d6102e/tests
```

The repository's root pytest configuration does not discover these generator-
local tests automatically, so retain this explicit command in review evidence.

## `lesson_probe.py`

Stages the selected task with the public runtime copier, invokes the actual
selected Racket authority through one persistent bridge, and dynamically reads
`LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, and `SEMANTIC_WITNESSES`. It audits
complete 3-demo/1-query lessons rather than isolated examples and therefore
checks that evidence survives the real lesson assembler.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/ba5056d6102e/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/lesson-probe-final.json \
  --timeout 1800
```

`run_with_racket.py` executes the inner command from `repo/`, so the
`../checks/...` output is packet-root-relative. The probe records source hashes,
exact sampler policy, cyclic schedule-start coverage, pair/profile counts,
exact-byte uniqueness, witness hits, rival survival, failures, and domain
limits. Rival names are read from the final generator rather than duplicated in
the probe.

Workspace drafts are never automatically selected.
