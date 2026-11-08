# Review workspace for 8881f54cf3c8

The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected.

## Files

- `baseline_generator_2.0.0.py` — byte-for-byte imported source, SHA-256
  `bd8ced009c7db1f8fdfbde2fd0385dc3a530ba14b1b3eabdef6e4cfe8ff58f2d`.
- `episode_and_branch_alias_probe.py` — public-API review tool that:
  1. models production four-demo/one-query episodes for independent seeds,
  2. reports operation/order collapse and query-to-demo positional aliases,
  3. verifies every declared `CANONICAL_SHORTCUTS` callable against all usable
     canonical pairs,
  4. exhaustively searches all 12 single-key Boolean-operation substitutions,
     and
  5. searches actual generated inputs for a counterexample to each canonical-
     fitting branch alias.

## Reproduce before/after probe

Run from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/8881f54cf3c8/workspace/episode_and_branch_alias_probe.py \
  --generator generators/8881f54cf3c8/workspace/baseline_generator_2.0.0.py \
  --seeds 64 --out ../checks/shortcut-probe/before.json

python3 run_with_racket.py python3 \
  generators/8881f54cf3c8/workspace/episode_and_branch_alias_probe.py \
  --generator generators/8881f54cf3c8/generator.py \
  --seeds 64 --out ../checks/shortcut-probe/after.json
```

The baseline invocation exits 1 because it intentionally detects the collapsed
query support, the false canonical-shortcut declaration, and the undeclared
key-4/XOR alias. The final invocation exits 0, while retaining a nonblocking
warning that the period-4 query operation equals demo position 0.

## Run task-local tests and full checks

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 8881f54cf3c8 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests

python3 run_with_racket.py python3 -m arcpuzzles check 8881f54cf3c8 \
  --battery --phase after --out ../checks/after

python3 run_with_racket.py python3 -m arcpuzzles lesson-census 8881f54cf3c8 \
  --per-band 100 --timeout 1800 --out ../checks/lesson-census.json
```

Use new output paths for reruns. The probe and census expose canonical answers
and are review-only; do not use them during visible-only solve attempts.
