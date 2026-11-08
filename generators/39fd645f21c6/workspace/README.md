# Workspace

The selected implementation is `../generator.py`; workspace drafts are not selected automatically.

- `generator_v3_original.py` — immutable working copy of the selected v3.0.1 baseline used to compare the teaching distribution and self-check behavior.
- `probe_shortcuts.py` — reusable source-bound semantic probe. It loads the current generator and canonical pairs, iterates `CANONICAL_SHORTCUTS` / `LESSON_COMPETITORS`, verifies which rivals fit canonical demonstrations, samples 100 lessons per difficulty band, materializes one counterexample per declared rival, and tests all four cyclic query rotations for each lesson.

The probe's final report is `checks/shortcut-probe-final.json`. It is diagnostic evidence, not an output authority; canonical outputs in supported receipts still come from the pinned Racket rule.
