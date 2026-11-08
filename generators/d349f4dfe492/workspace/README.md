# d349f4dfe492 review workspace

The selected implementation is `../generator.py`; files here are reusable,
source-bound review probes and are never selected as production generators.

## Contract/curriculum probe

Run from `repo/`:

```bash
python3 generators/d349f4dfe492/workspace/contract_probe.py \
  --out ../checks/contract-probe.json
```

It verifies all canonical pairs against the Python mirror, checks that every
advertised `(grid_h, grid_w, n_seeds)` Cartesian combination works in every
band, calibrates every declared `CANONICAL_SHORTCUTS` function against all
canonical pairs, tests every cyclic three-demo start against the generator's
actual `LESSON_COMPETITORS`, and reports profile/witness coverage. It exits
nonzero and retains exact reproducers in JSON on any failure.

The probe intentionally does **not** invoke or expose the private Racket rule.
Use the packet's supported `arcpuzzles check ... --stage rule_smoke` and
`authority_sync` stages for authority parity.

## Racket parity probe

Run through the packet wrapper so the offline Racket runtime is available:

```bash
python3 run_with_racket.py python3 \
  generators/d349f4dfe492/workspace/racket_parity_probe.py \
  --out ../checks/racket-parity.json
```

This batches generated examples from all bands/profiles through the supported
`arcpuzzles apply` command, compares every pixel with `rule_mirror`, and binds
the report to both the selected rule hash and generator SHA-256.
