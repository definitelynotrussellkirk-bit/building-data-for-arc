# Workspace probes

The selected implementation is `../generator.py`; these files are reusable diagnostics, not alternate generators.

## `reference_probe.py`

Builds an independent Python oracle for the intended rule and the generator's declared rivals. It verifies every declared canonical shortcut against the canonical pairs, searches the production sampler for a disagreement, and emits a replayable JSON report.

From the repository root:

```bash
python3 generators/1a92a12bac06/workspace/reference_probe.py \
  --out ../checks/contract-probe.json
```

The retained report binds generator SHA `841808457e0df267dd807319c83f015efa4a28772704ec4b4f73e0c5592f4859` and rule hash `6d628a0b1a7d`.

## `schedule_probe.py`

Enumerates all four cyclic starts of the deterministic schedule, materializes three demonstrations plus one query, holds out each position in turn, and tests `lesson_identifiable` plus every declared `LESSON_COMPETITORS` rival.

```bash
python3 generators/1a92a12bac06/workspace/schedule_probe.py \
  --seeds 100 --out ../checks/schedule-exhaustive.json
```

The retained run covered 1,200 lessons and 4,800 query rotations over 100 seeds per difficulty band with zero ambiguity or hook failure.
