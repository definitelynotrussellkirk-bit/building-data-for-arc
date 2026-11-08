# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected.

- `reference_probe.py` is the portable independent oracle/probe library used by
  task tests. It loads canonical pairs through `reviewer_support`, extracts the
  4×6 tile lattice, evaluates the intended rule and six named rivals, computes
  exact grid diffs/hashes, and can execute the canonical Racket authority.
- `generator-v3.1.0-baseline.py` preserves the reviewed baseline for diagnosis.
- `progress.md` records the root cause, RED→GREEN evidence, semantic ruling,
  final source hash, and replay status for the next reviewer.

Run the focused contract from the packet root with:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 79a30e61d332 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```
