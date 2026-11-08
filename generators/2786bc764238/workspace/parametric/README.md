# Native parametric family: `2786bc764238`

This family preserves the selected canonical rule byte-for-byte as the default
and varies only **which component-ranking statistic feeds the final crop**.

## Contract

- Parameter: `selection_metric`
  - `cell_count` — exact canonical default; choose the unique component with the
    most occupied cells.
  - `bbox_area` — choose the unique component with the largest bounding-box
    area.
- Demonstrations: 2–6.
- Private query bank: exactly four distinct queries.
- Input generation is independent of the private setting.
- Every demonstration makes the two metrics select different components.
- The query bank includes a 9×12 lower-bound case and a substantive 30×30 case.

## Sequential dependency

1. **A:** extract nonzero 4-connected components and rank them by the selected
   metric.
2. **Intermediate:** the selected component, including its source-grid bounding
   box.
3. **B:** crop the original multicolor input to that selected bounding box.

The crop bounds cannot be fixed before A selects a component.  The protected
causal witness is built after authoring preflight and retained under
`WORK/checks/2786bc764238/causal/` in the return package.

## Files

- `adapter.py` — deterministic native episode generator and exact Racket
  programs.
- `promotion.json` — finite adapter contract.
- `canonical.rkt` — exact catalog program bytes.
- `audit.py` — reusable independent bounded audit.
- `evidence/current/audit-summary.json` — current bounded audit result.

## Reproduce focused checks

From `WORK/repo`:

```bash
PYTHONPATH=src:shared/runtime pytest -q --import-mode=importlib \
  generators/2786bc764238/tests
python3 generators/2786bc764238/workspace/parametric/audit.py \
  --seeds 8 --demos 2 6 \
  --out generators/2786bc764238/workspace/parametric/evidence/current/audit-summary.json
```

From the packet root, run the staged suite and protected authoring preflight:

```bash
python3 review.py task-tests 2786bc764238 --phase after \
  --out ../checks/2786bc764238-tests
python3 review.py run python3 \
  generators/2786bc764238/workspace/parametric/preflight_compat.py \
  2786bc764238 --out ../checks/2786bc764238/qualification
```

The task-local preflight entry point only normalizes a catalog split stored as a single pair object into the one-element list expected by the packet preflight; all source binding, base replay, generation checks, worker execution, and protected-Racket receipt creation remain delegated to the official implementation.

The audit and preflight are finite reviewer evidence.  They do not grant source
approval, native acceptance, or training admission.
