# Task workspace

The selected implementation is `../generator.py`. Workspace material is
supporting authoring evidence and is never automatically selected.

- `probe_shortcuts.py` checks the generator's actual `CANONICAL_SHORTCUTS`
  declaration against all labeled canonical pairs and searches emitted
  generalized inputs for a disagreement witness.
- `parametric/` contains the proposed episode-level `selector_role` extension,
  its exact Racket programs, public-challenge projection, and verifier.

Canonical repair evidence is retained under `WORK/checks/`; the workspace code
is covered by task-local portable tests.
