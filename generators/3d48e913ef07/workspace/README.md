# Review tools for `3d48e913ef07`

`reference_probe.py` is an independent Python reconstruction of the written task,
not an import of generator-private helpers. It provides:

- canonical-pair and validator checks;
- deterministic per-band distribution counts;
- executable comparisons against the generator's actual `SEMANTIC_RIVALS`;
- verification that every declared `CANONICAL_SHORTCUTS` rule really fits every
  usable public pair;
- all cyclic query rotations of the five-profile production schedule, using the
  generator's actual `LESSON_COMPETITORS` declarations; and
- optional batch parity against the protected canonical Racket authority.

From the extracted packet root:

```bash
python3 run_with_racket.py python3 \
  generators/3d48e913ef07/workspace/reference_probe.py \
  --count 250 --cycles-per-band 100 --racket \
  --out ../checks/independent-audit.json
```

The wrapper runs Python from `repo/`, supplies `src` and `shared/runtime`, and
activates the packet's verified Racket binary. The output path is therefore
relative to `repo/`. The command exits nonzero for canonical/oracle mismatches,
validator failures, nondeterminism, cyclic lesson failures, dishonest canonical
shortcut declarations, or Racket parity failures.

Task-local regressions live in `../tests/`. Run them through the packet's
`task_tests` stage so the source and tools are snapshotted into a portable
runtime; the repository-wide pytest command does not discover them automatically.
