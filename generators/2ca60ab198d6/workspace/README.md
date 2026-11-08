# Task-local review tools — 2ca60ab198d6

The selected implementation is `../generator.py`. The tools here are review
probes, not alternate generators or label authorities.

## Exhaustive cyclic lesson probe

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 -B \
  generators/2ca60ab198d6/workspace/cyclic_lesson_probe.py \
  --seeds 32 --starts 16 --out ../checks/cyclic-lesson-probe.json
```

The probe crosses every requested seed and cyclic start with `easy`, `medium`,
and `hard`. For each start it materializes four consecutive demonstrations plus
the next query, checks that all four schedule profiles occur in the demos, runs
the generator's self-check, verifies every declared lesson rival is refuted,
and records witness/profile/unique-input counts. It also checks all 432 boundary
combinations of the six exact override axes. Canonical shortcuts are read from
the generator declaration and verified against all canonical pairs rather than
copied into the probe.

The report is source-hashed and refuses to overwrite existing evidence. It is a
finite declared-rival audit, not a proof of universal identifiability, and its
Python mirror does not replace the repository's Racket rule-smoke and authority
checks. Use `--skip-axes` only when a faster schedule-only diagnostic is needed.
