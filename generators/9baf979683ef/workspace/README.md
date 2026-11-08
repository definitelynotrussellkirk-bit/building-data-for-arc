# Workspace

The selected implementation is `../generator.py`; workspace files are reusable
review tools and are never automatically selected.

## `audit_distribution.py`

A source-bound task-local audit that imports the selected generator and its
actual `CANONICAL_SHORTCUTS` / `LESSON_COMPETITORS` declarations. It checks:

- exact input uniqueness and validator/strict-profile acceptance by band;
- realized counts for every declared control;
- canonical-profile frequency;
- whether each canonical-fitting shortcut is refuted by sampled scenes; and
- every cyclic choice of query within deterministic four-pair lesson windows.

Run from `repo/` through the packet wrapper:

```bash
python3 ../run_with_racket.py python3 \
  generators/9baf979683ef/workspace/audit_distribution.py \
  --per-band 100 --cyclic-windows 100 \
  --out ../checks/task-local-audit.json
```

The retained final report is `checks/task-local-audit-final.json`. The probe is
finite and declaration-based; zero surviving declared rivals is not a proof of
universal induction.
