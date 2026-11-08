# Workspace

`qualify_lessons.py` is a task-local, source-bound curriculum probe. It discovers the selected generator's declared rivals, verifies canonical parity through `rule_mirror`, materializes an explicit deterministic schedule of complete lessons, and records unique-input, witness, and rival-survival counts.

From the packet root:

```bash
python3 repo/generators/b3bfd59c2c43/workspace/qualify_lessons.py \
  --per-band 100 \
  --out repo/generators/b3bfd59c2c43/workspace/qualification.json
```

The retained `qualification.json` is bound to the generator SHA-256 written inside it. This probe complements, rather than replaces, the Racket-backed battery authority checks.
