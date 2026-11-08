# Workspace

The selected implementation is `../generator.py`; workspace tools are evidence and are never automatically selected.

- `reference_probe.py` independently analyzes components, embeds the three verified canonical pairs, computes the intended height-ranked output and four plausible rival outputs, and loads an arbitrary generator path through `GENERATOR_UNDER_TEST`.
- `lesson_probe.py` uses the public isolated `arcpuzzles.runtime.generate` path and canonical Racket labels to census complete 3-demo/1-query lessons. Run from the packet root with:

  `python3 run_with_racket.py python3 generators/4c04ce6c5477/workspace/lesson_probe.py --lessons-per-band 100 --out ../checks/probes/4c04ce6c5477_lessons_final_a21a.json`

The retained review census is finite and source-bound; it tests the declared rival set, not universal rule induction.
