# Parametric family: row fill and equal-color gap bridge

`row_policy` has two episode-fixed settings:

- `first_fill` — exact canonical rule: fill each nonblank row with its leftmost nonzero color.
- `bridge_equal` — first construct that row-filled grid, then fill a blank row only when the nearest filled rows above and below have the same intermediate color.

The native adapter supports 2–6 demonstrations and 1–4 queries. Inputs are deterministic, prefix-stable, and identical across settings for the same request. The four-query bank includes a substantive 30×30 case.

Useful files:

- `adapter.py`: promotion interface.
- `prototype.py`: sampler, independent Python semantics, and finite teaching check.
- `canonical.rkt` / `bridge-equal.rkt`: executable setting programs.
- `rightmost-bridge.rkt`: wrong-intermediate causal counterfactual.
- `audit.py`: reusable boundary, determinism, named-rival, and optional protected-Racket audit.
- `promotion.json`: finite settings and request contract.

From the repository root, a future reviewer can rerun the bounded audit with protected Racket using the packet wrapper:

```sh
python3 ../run_with_racket.py python3 generators/7092d9933e2d/workspace/parametric/audit.py --out ../checks/7092d9933e2d-audit.json
```

The audit is finite evidence, not a proof of universal identifiability. Owner exact-source review and native acceptance remain separate.
