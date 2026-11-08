# Workspace tools for `48732ebd41f9`

The selected implementation is `../generator.py`; files here are reproducible
review probes, not alternate generators.

## `semantic_probe.py`

Runs a source-hashed task-local census using an independent Python oracle for
the selected rectangle rule. It reads the generator's actual
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, schedule, and
axes rather than copying names into the probe.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/48732ebd41f9/workspace/semantic_probe.py \
  --lessons-per-band 100 \
  --out ../checks/48732ebd41f9_semantic_probe.json
```

The default tests 100 four-demonstration lessons in each of easy, medium, and
hard. Twenty-five lessons use each cyclic schedule start. The report records
source hashes, exact sampler formulas, unique-input counts, canonical-profile
support, witness counts, and per-rival lesson disagreement counts. It exits
nonzero for invalid draws, oracle divergence, observation failures, or a named
rival that remains unresolved on a query after fitting every demonstration.
