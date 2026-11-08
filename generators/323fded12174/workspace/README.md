# Workspace

The selected implementation is `../generator.py`.

`rival_probe.py` is a retained, reusable semantic probe. It discovers the
current `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`
directly from the generator, verifies every shortcut against all five canonical
pairs, samples all three difficulty bands, and checks every cyclic two-demo
lesson window. Run from the packet root:

```bash
python3 repo/generators/323fded12174/workspace/rival_probe.py \
  --samples-per-band 24 --seed-base 323 \
  --out checks/rival-probe.json
```

The command exits nonzero on an invalid generated input, a missing witness, a
surviving declared rival, or an unidentifiable cyclic lesson.
