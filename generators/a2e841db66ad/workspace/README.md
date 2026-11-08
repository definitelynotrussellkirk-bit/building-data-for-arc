# Shortcut probe

`shortcut_probe.py` is a retained source-bound helper for this generator. It
loads the selected generator through `reviewer_support`, iterates the live
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`
declarations, checks every labeled canonical pair, searches generated inputs for
an exact counterexample, and checks every query rotation in consecutive lesson
windows.

From the repository root:

```bash
PYTHONPATH=shared/runtime:shared python3 \
  generators/a2e841db66ad/workspace/shortcut_probe.py \
  --per-band 16 --starts 8 --out ../checks/shortcut-probe.json
```

The Python mirror is a fast authoring oracle. Retain a separate `arcpuzzles
apply` receipt for any counterexample claimed as authoritative Racket evidence.
