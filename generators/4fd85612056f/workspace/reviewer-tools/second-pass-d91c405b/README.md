# Portable second-pass tools

These tools operate on the returned review response; they do not edit the reviewed repository.

## `verify_response.py`

Checks either an extracted response directory or a response ZIP:

- safe/unique archive paths and ZIP CRCs;
- every root hash declared by `INTAKE.json`;
- `EVIDENCE-BUNDLE.tar.gz` hash, inventory, sizes, and all member hashes;
- exact agreement between the patch and declared changed paths;
- existence of every evidence path named by verification receipts;
- assignment, packet, task, completion, solve, and generator-hash bindings.

With `--original-worktree`, it also verifies all baseline file hashes from `ASSIGNMENT.json` and runs `git apply --check` against that worktree. It does not apply anything.

```bash
python second-pass/verify_response.py . --json
python second-pass/verify_response.py response.zip --json
python second-pass/verify_response.py . --original-worktree /fresh/WORK --json
```

## `fuzz_generator.py`

Loads the shipped final generator under a deterministic minimal context and checks properties independent of the repository RNG implementation: exact overrides, validation, determinism, public-manifold invariants, named shortcut separation, schedule rotations, invalid requests, and mutation fixtures.

```bash
python second-pass/fuzz_generator.py solve/source/generator.py --preset quick
python second-pass/fuzz_generator.py solve/source/generator.py --preset full \
  --json-out second-pass/reports/generator-structural-fuzz-full.json
```

This is supplementary. The production-runtime and Racket authority claims remain in the sealed evidence bundle.

## Tests

```bash
python -m unittest discover -s second-pass/tests -p 'test_*.py' -v
```
