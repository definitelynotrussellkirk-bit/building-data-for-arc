## 204eaaff6c24
**Reproduced defect.** Current source SHA-256:
`9c475e402957455e63e43cc2645867c23a74b1cb0b4dcdaf54909c066072839f`;
selected rule hash: `4571597a8055`.

The public generator API accepts malformed controls instead of rejecting them:

- `n_cells=2.7` is accepted and coerced to an integer-two result;
- `n_cells=True` is accepted as one foreground cell;
- an unknown override key is silently ignored and produces the default grid.

It also rejects a feasible semantic request when dimensions are left free:
`seed=17`, `sample_index=0`, `difficulty=medium`,
`n_cells=8`, `fg_layout=diagonal`, `fg_color=4` raises because a sampled 4×6
grid has capacity four. The same request with explicit `grid_h=8, grid_w=8`
succeeds, passes `self_check`, and has exactly eight diagonal color-4 cells.
The protected Racket receipt returns the expected 1×8 color-4 bar.

The exact reproducer, inputs, outputs, hashes, and commands are retained in:

- `checks/audit/204eaaff6c24/reproduction.json`;
- `checks/audit/204eaaff6c24/reproduce.py`;
- `checks/audit/204eaaff6c24/input.json`;
- `checks/audit/204eaaff6c24/racket.json`.

The isolated audit also found no portable task tests and a failed semantic gate
because the source declares no `strict_canonical_like`, `SEMANTIC_WITNESSES`,
`SEMANTIC_RIVALS`, or `lesson_identifiable` contract
(`checks/audit/204eaaff6c24-combined/checks/204eaaff6c24_audit_summary.json`).
Defect lint reported 134 warnings: 132 strict-scalar findings,
`selfcheck-power`, and `selfcheck-minimal-impostor`
(`checks/audit/204eaaff6c24-defect-lint/checks/204eaaff6c24_audit_defect_lint.log`).
I did not edit this audit target.
