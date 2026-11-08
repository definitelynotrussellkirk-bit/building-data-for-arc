# Workspace

`lesson_probe.py` is the retained source-bound semantic census for this task. It computes labels with its own 4-connected-component oracle, compares the selected generator's Python mirror to that oracle, and dynamically iterates the generator's current `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, and `SEMANTIC_WITNESSES` declarations.

From the packet root:

```bash
PYTHONPATH=repo/src:repo/shared/runtime:repo \
python3 repo/generators/00f0de29a65c/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out checks/00f0de29a65c_lesson_census.json
```

The deterministic sampler uses easy/medium/hard bands, 100 lessons per band by default, four consecutive demonstrations plus one query per lesson, and records generator/probe/canonical source hashes. It reports unique inputs, oracle disagreements, final-grid failures, strict-profile counts, witness hits, and per-rival lesson survival. It is a task-local regression/audit tool, not evidence that the rule is identifiable under every possible ARC lesson distribution.
