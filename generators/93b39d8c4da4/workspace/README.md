# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Distribution qualification

Run the source-bound complete-lesson probe from the packet repository environment:

```text
python3 generators/93b39d8c4da4/workspace/qualify_distribution.py \
  --generator generators/93b39d8c4da4/generator.py \
  --canonical shared/data/canonical/puzzles.jsonl \
  --lessons-per-band 100 \
  --seed-base 930000 \
  --out ../checks/93b39d8c4da4_final_300_lesson_probe.json
```

The tool discovers `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `SCHEDULE_PROFILES`, and `EXAMPLES_NEEDED` from the loaded generator. It verifies every claimed canonical shortcut against all usable canonical pairs, tests every cyclic schedule start, and reports unique-input counts, witness/rival disagreements, exact axis distributions, and lesson-identifiability failures.

The retained final report uses 100 lessons per difficulty band, four demonstrations plus one query per lesson, and generator SHA-256 `1a96c0f22e24c4f68622675e5b96865edba6e8781da9192dcee68feacf43cb1e`.
