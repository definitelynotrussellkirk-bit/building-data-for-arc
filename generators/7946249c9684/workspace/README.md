# Workspace

The selected implementation is `../generator.py`; workspace scripts are review
tools and are never selected as the generator.

## `curriculum_probe.py`

A source-bound complement to the shared Racket-backed lesson census. It:

- reads rival names directly from the generator;
- verifies every declared canonical shortcut on every public pair;
- rotates every member of a four-instance schedule window into the query slot;
- checks all three cyclic schedule starts in every difficulty band; and
- exhausts a compact 486-case joint override matrix across all profiles/bands.

Run from the packet root so the verified runtime is selected:

```bash
python3 run_with_racket.py python3 generators/7946249c9684/workspace/curriculum_probe.py \
  --blocks-per-band 100 --out ../checks/curriculum-probe.json
```

The probe uses the task-local Python mirror for speed; pair it with the shared
`arcpuzzles lesson-census` report, which binds outputs to the Racket authority.
