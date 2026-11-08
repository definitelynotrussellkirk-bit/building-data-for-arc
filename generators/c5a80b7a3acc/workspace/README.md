# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Saved lesson audit

`audit_lessons.py` reads the shared public census and its retained Racket labels.
From the packet root, run:

```bash
python3 repo/generators/c5a80b7a3acc/workspace/audit_lessons.py \
  --census checks/lesson-census-final.json --out checks/lesson-tool/new-cyclic-audit.json
```

Choose a new output path for each run. The audit binds the selected generator
and canonical authority, checks every declared canonical shortcut on all usable
canonical pairs, preserves rival namespaces, and tests all six cyclic query
choices with five demonstrations. It records exact generated witnesses, refuted
rivals, surviving rivals, ambiguous queries, unique inputs, and distribution
counts. Accepted sample indices are recovered using input-only generator replay;
labels always come from the saved census. Exit 1 reports ambiguity, missing
witnesses, or errors. Finite rival refutation does not prove universal uniqueness.

## Bounded witness-pool proof check

```bash
python3 repo/generators/c5a80b7a3acc/workspace/check_witness_pools.py \
  --out checks/new-witness-pool-audit.json
```

This independently enumerates each distinct AND/XOR witness shape pair, checks
the live rival declarations and validator at a lawful representative placement,
and records source hashes and the intersection of guaranteed refutations.
Its labels are diagnostic Python set calculations; it does not claim per-pair
Racket execution or exhaustive placement coverage. The construction proof is
in `../notes.md`. It also requires a new output path.
