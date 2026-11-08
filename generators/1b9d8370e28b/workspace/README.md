# Workspace

`rival_probe.py` is the reusable, source-bound semantic census for this repair.
Run it from the packet root so the selected runtime is on `PYTHONPATH`:

```bash
python3 run_with_racket.py python3 \
  generators/1b9d8370e28b/workspace/rival_probe.py \
  --lessons-per-band 100 --base-seed 910000 \
  --out ../checks/1b9d8370e28b_rival_probe.json
```

The probe hashes the exact generator it imports, iterates the generator's own
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`, checks
all canonical pairs, assembles deterministic lessons in each difficulty band,
and records uniqueness, strict-domain failures, witness frequencies, rival
disagreements, first counterexamples, and sampling limits.

Generated labels use the task-local Python `rule_mirror`; the report explicitly
limits that evidence and must be read with the retained source-bound Racket
`rule_smoke` and authority-sync reports. Workspace drafts are never selected
automatically; `../generator.py` is the selected implementation.
