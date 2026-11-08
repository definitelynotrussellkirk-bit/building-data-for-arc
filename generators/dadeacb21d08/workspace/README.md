# Workspace

The selected implementation is `../generator.py`; workspace drafts are never selected automatically.

## Independent distribution audit

`audit_distribution.py` is a source-local reviewer tool. It imports the selected generator, verifies all usable canonical pairs against the task-local mirror, confirms that every declared canonical shortcut really fits those pairs, exhausts the 192 joint boundary combinations of the public axes, samples per-band distributions, and tests every cyclic start of the four-profile lesson schedule against the generator's actual `LESSON_COMPETITORS` declarations.

Run from this task directory:

```bash
python3 workspace/audit_distribution.py \
  --per-band 100 \
  --lessons-per-band 100 \
  --out ../../../checks/independent-audit-final.json
```

The retained final report is bound to generator SHA-256 `ab33a55161bca6aa2ac3fa0a061e148e3b86816efb56ee17d0a1ef8e0578e749`. It reports 192/192 boundary combinations, 300/300 unique sampled inputs, 300/300 identifiable cyclic lessons, and no surviving declared competitor. This is finite rival evidence; Racket-based shared gates remain the semantic authority.
