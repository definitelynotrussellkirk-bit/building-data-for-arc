# Workspace

`probe_shortcuts.py` is a reusable source-driven verifier for this generator. It imports the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies canonical fit claims, searches production draws for emitted counterexamples, and checks every cyclic four-demo schedule window. It intentionally does not copy a rival-name list.

The selected implementation remains `../generator.py`; workspace drafts are never automatically selected.
