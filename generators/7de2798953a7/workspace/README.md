# Workspace

The selected implementation is `../generator.py`; workspace files are probes,
not alternate selected generators.

- `reference_probe.py` is an independent Python oracle plus three rival rules,
  canonical-pair loader, exact shortcut witness, and real-Racket parity helper.
- `audit_distribution.py` audits determinism, exact canonical profiles,
  semantic witnesses, declared rivals, every query rotation for configurable
  cyclic starts, and optional Racket parity. Example:

  ```bash
  python3 run_with_racket.py python3 \
    generators/7de2798953a7/workspace/audit_distribution.py \
    --count 200 --windows 100 --racket \
    --out ../checks/distribution-audit-final.json
  ```

The audit intentionally makes only finite claims about the declared rival set;
it is not a proof of unique induction over arbitrary programs.
