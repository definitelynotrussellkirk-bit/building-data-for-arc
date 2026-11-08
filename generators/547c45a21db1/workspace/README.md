# Reusable review tools

The selected implementation is `../generator.py`. Workspace tools and proposals
are never automatically selected. Run the commands below from the extracted
**packet root** after applying `patches/source.patch`. The Racket wrapper runs
its payload from `repo/`.

## Portable verification

If host Python imports pytest but the isolated runner cannot, use:

```sh
python3 setup_racket.py
python3 repo/generators/547c45a21db1/workspace/bootstrap_test_env.py --out .review/test-env --report checks/environment/bootstrap.json
.review/test-env/bin/python run_with_racket.py ../.review/test-env/bin/python -m arcpuzzles check 547c45a21db1 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-replay
```

The helper copies installed pytest, pluggy, iniconfig, packaging and pygments
into a new Linux venv and records file hashes. It downloads nothing and refuses
an existing output directory. It relies on host system packages for NumPy/Pillow
and verifies all imports with `-E -s`; it is not a self-contained environment
archive. A normal venv with the packet's declared dependencies is also suitable.

## Semantic and geometry probes

- `semantic_review/final_probe.py` reads the generator's actual declarations,
  checks canonical fits and production/rotation scores against saved Racket
  labels, and extracts generated witnesses and rejected-index exceptions.
  Its README and `checks/semantic-final/commands.json` give exact invocations.
- `semantic_review/probe.py` retains independent exploratory rivals and the
  first separating witness; Python predictions are diagnostic.
- `semantic_review/even_length/enumerate_paths.py` finds contrasting even
  geometry by exhaustive induced-path enumeration on the minimum board.
- `../tests/test_path_contract.py` covers validation and all joint axes;
  `../tests/test_lesson_contract.py` covers parity, cyclic starts, rotations
  and the exact failed intermediate examples.

## Optional shared-tool proposal

`tooling_proposal/semantic_gate_declared_rivals.patch` scores declared rivals
even without a custom lesson hook. It is a separate maintainer decision and
applies from the **repository root**. Its disposable-copy verification has
13 regression passes and 106 semantic-module passes. See that directory's
README and the return's feedback F1.

## Compressed evidence

If the return contains `EVIDENCE-BUNDLE.README.md`, restore that verified bundle
first. The earlier census is additionally compressed losslessly as
`checks/lesson-census.json.gz`; the final census remains ordinary JSON.
`checks/compressed-evidence.json` records original path, size and SHA-256.
Restore with:

```sh
python3 repo/generators/547c45a21db1/workspace/restore_compressed_evidence.py --root . --manifest checks/compressed-evidence.json
```

The helper verifies both hashes, confines paths to the chosen root and refuses
to overwrite different evidence. All failures remain retained.
