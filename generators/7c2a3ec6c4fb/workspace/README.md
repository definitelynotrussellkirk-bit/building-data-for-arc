# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

## Review aids

- `generator_v2_2_0_baseline.py` preserves the pre-review implementation.
- `shortcut_census.py` discovers low-complexity component signatures that solve the canonical examples, measures how often they survive generated data, and checks answer morphology, free-placement coverage, observable controls, and semantic-witness support.

Run the reusable guardrail from the repository root:

```bash
PYTHONPATH=shared/runtime:src python3 \
  generators/7c2a3ec6c4fb/workspace/shortcut_census.py \
  --samples 5000 --layout-samples 1000 --check \
  --out ../checks/shortcut_census.json
```

A nonzero exit means the census found a strict failure, undeclared canonical-perfect shortcut, collapsed answer/control coverage, weak semantic witness support, or regression to the old placement lattice.


## Connectivity and portable-runtime probes (v3.2.0)

`connectivity_census.py` uses its own foreground flood fill, not generator component helpers. It records source identities, exact seed/index protocol, every failure, the first counterexample per stratum, and optionally actual Racket labels for every sample. It reads only public canonical pairs and generated inputs, never solve-private answers. It is task-local: its standard `rule!` lambda binding is not a general Racket syntax converter.

From the extracted packet root, compare the immutable v3.1.0 baseline with the selected generator:

```bash
python3 run_with_racket.py python3 \
  generators/7c2a3ec6c4fb/workspace/connectivity_census.py \
  --generator ../.review/baseline/repo/generators/7c2a3ec6c4fb/generator.py \
  --samples 1800 --racket --out ../checks/connectivity-before-replay.json

python3 run_with_racket.py python3 \
  generators/7c2a3ec6c4fb/workspace/connectivity_census.py \
  --samples 1800 --racket --out ../checks/connectivity-after.json
```

The immutable baseline is supplied by the review packet; it is not copied into this workspace. For another archived version, pass its generator file explicitly. Omitting `--racket` is a Python-only analysis, not independent label verification.

`review_probes.py` prepares and imports a fresh runtime for this task plus audit targets `40b155c46f6e` and `bb1b1e111e1a`, checks source-path isolation, executes real Racket, and writes exact audit counterexamples. The target IDs are explicit constants for this assignment, not a generic automatic audit selector.

```bash
python3 run_with_racket.py python3 \
  generators/7c2a3ec6c4fb/workspace/review_probes.py --out ../checks/audits

python3 -m pytest -q repo/generators/7c2a3ec6c4fb/tests
```

These packet-root commands preserve the selected Racket runtime environment. The worker records its actual temporary directory and is import-isolated, not OS-sandboxed. All new tests are task-local and must be invoked explicitly because the repository-wide pytest configuration does not discover them.

The shortcut census retains at most 20 invalid examples but reports the true failure count and valid-input denominator. Its witness counts overlap within inputs. Do not add witness counts or combine different seed protocols as unique sample totals.
