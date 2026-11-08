# Workspace

The selected implementation is `../generator.py`. Files here are independent review probes and are not selected automatically.

## `reference_probe.py`

Task-local canonical parser and independent beam oracle. It does not import generator implementation helpers. The regression tests use it for canonical parity, blocker functionality, exact observed controls, and shortcut counterexamples.

## `lesson_probe.py`

Mirrors the production per-puzzle accepted-prefix sampler, evaluates the generator's actual `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS`, and writes source-hash-bound JSON evidence.

From the packet root:

```bash
PYTHONPATH="$PWD/repo/shared/runtime:$PWD/repo/generators/510b12f6a12a/workspace" \
python3 repo/generators/510b12f6a12a/workspace/lesson_probe.py \
  --generator repo/generators/510b12f6a12a/generator.py \
  --lessons-per-band 100 --pairs-per-lesson 4 --base-seed 51012000 \
  --require-complete-refutation \
  --json-out checks/lesson_probe_100_per_band.json
```

The probe records global unique-input counts but follows production policy: duplicates are forbidden within a lesson, not across independent lessons.
