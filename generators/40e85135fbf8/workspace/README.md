# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Generate checked lessons

From the review packet root:

```bash
python3 run_with_racket.py python3 \
  generators/40e85135fbf8/workspace/generate_checked_lessons.py \
  --seed 17 --count 3 --difficulty medium --allow-unapproved \
  --out ../checks/new-checked-lessons.jsonl
```

The helper requests the generator's six demonstrations, derives labels through
the public Racket-backed API, checks the returned teaching contract, and writes
only validated complete episodes. `--allow-unapproved` is the existing explicit
research opt-in for a not-yet-integrated source; it grants no approval. Use a new
output path. Generic `arcpuzzles generate/export` callers must explicitly set
`--train 6` for this task; their global defaults have not been changed.
Preserve demonstration order and following-query selection. Arbitrary query
rotations are not supported by the six-demo guarantee.

## Inspect color roles and declared rivals

```bash
python3 run_with_racket.py python3 \
  generators/40e85135fbf8/workspace/probe_palette_roles.py \
  --seed-start 0 --seed-count 12 --sample-start 0 --sample-count 36 \
  --out ../checks/new-palette-role-probe.json
```

This diagnostic records exact seeds/indices, generator/probe/rule hashes,
canonical shortcut fit, unique-input counts, absence ranks on each axis and
every declared rival namespace. Generated labels here are explicitly Python
mirror labels. For Racket-labelled production evidence use `arcpuzzles
lesson-census 40e85135fbf8 --per-band 100 --rotate-query --rotation-policy
diagnostic` with a fresh output path. The final review's production census
passed, while its rotation diagnostic retained real ambiguities.
