# Workspace / next-agent handoff

The selected implementation is `../generator.py`; focused tests are in `../tests/test_generator_c3dcd7ae3aaf.py`.

## Reproduce the focused contract

```bash
cd repo
pytest -q generators/c3dcd7ae3aaf/tests/test_generator_c3dcd7ae3aaf.py
```

## Reproduce the full generator battery

From the packet root:

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check \
  c3dcd7ae3aaf --battery --phase after --out ../checks/after-recheck
```

Use a fresh `--out` directory for each invocation.

## Design invariants worth preserving

- Keep all normal examples contrastive; do not remove the L-triomino or domino negatives.
- Keep at least one horizontal and one vertical target, and at least two targets total.
- Keep both edge and interior targets so position is not predictive.
- Do not expose a public axis unless `observe_overrides` can recover it exactly.
- Every public override value must remain legal in every difficulty band.
- Do not change the Racket rule without updating `RULE_HASH` and rechecking every canonical pair.
