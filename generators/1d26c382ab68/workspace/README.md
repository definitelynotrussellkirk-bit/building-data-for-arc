# Workspace: 1d26c382ab68

The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

## Review contract added in `review-eeb8697721e28693`

The generated instances and selected Racket rule were intentionally left unchanged. The reusable addition is an executable teaching contract:

- `SEMANTIC_RIVALS` / `LESSON_COMPETITORS`: `always_left`, `exact_orientation_only`, `accept_reflection`, `all_same_size`.
- `CANONICAL_SHORTCUTS`: proves `always_left` fits all four public canonical pairs.
- `WITNESS_RIVALS`: binds generated counterexamples to the rivals they refute.
- `lesson_identifiable`: rejects a lesson when a declared rival fits every demonstration but predicts a different query output.

Focused checks from the packet root:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 1d26c382ab68 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
python3 run_with_racket.py python3 -m arcpuzzles check 1d26c382ab68 \
  --stage semantic_gate --require-rotations-identifiable --timeout 1800 \
  --phase after --out ../checks/required-rotations-final
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 1d26c382ab68 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json
```

Do not infer universal identifiability from these finite rivals. When adding a new plausible shortcut, add the callable to the declarations and a generated witness that refutes it before relying on the lesson census.
