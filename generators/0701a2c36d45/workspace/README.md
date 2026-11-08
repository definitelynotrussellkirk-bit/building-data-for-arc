# Workspace tools

The selected implementation is `../generator.py`; workspace files are authoring and audit helpers only.

- `review_probe.py` independently reconstructs panel chunks, rotations, vote counts, realized texture, exact controls, and mirror output from returned pixels. It deliberately does not import production parsing or rule helpers.
- `cyclic_lesson_probe.py` enumerates every residue of the six-step schedule in easy, medium, and hard bands, materializes five consecutive pairs, holds out each pair once, and scores the generator's live `LESSON_COMPETITORS`. Its labels come from `review_probe.vote_profile`, not the production mirror.

Example from the packet `repo/` directory:

```bash
PYTHONPATH=shared/runtime:generators/0701a2c36d45/workspace \
  python3 generators/0701a2c36d45/workspace/cyclic_lesson_probe.py \
  --out ../checks/cyclic-lesson-probe.json
```

The cyclic probe is finite, mirror-labelled evidence. Use the source-bound `arcpuzzles lesson-census` command for authority-labelled production population checks.
