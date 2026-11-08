# Native parametric family: `15df00eb9323`

This family preserves the selected canonical majority-overlay rule byte-for-byte
as the default and varies the consensus threshold applied to the same normalized
support-count intermediate.

## Contract

- Parameter: `consensus_level`
  - `majority` — exact canonical default; retain normalized cells occupied by at
    least two source blobs.
  - `unanimous` — retain only normalized cells occupied by all three blobs.
- Demonstrations: 2–6.
- Private query bank: exactly four distinct queries.
- Input generation is independent of the private setting.
- Every generated input has support counts exactly `{1, 2, 3}`, so union,
  majority, and unanimity are visibly distinct.
- The query bank includes a 7×11 lower-bound case and a substantive 30×30 case.

## Sequential dependency

1. **A:** extract each isolated blob, crop it to its own bounding box, align the
   normalized crops at their top-left corners, and count support per coordinate.
2. **Intermediate:** the normalized support-count map.
3. **B:** threshold that map at two or three, paint surviving cells cyan, and
   crop the result to content.

B depends on the input-derived counts emitted by A.  The protected causal witness
is built after authoring preflight and retained under
`WORK/checks/15df00eb9323/causal/` in the return package.

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
  generators/15df00eb9323/tests
python3 generators/15df00eb9323/workspace/parametric/audit.py \
  --seeds 40 --demos 2 6 \
  --out generators/15df00eb9323/workspace/parametric/evidence/current/audit-summary.json
```

From the packet root, run the staged suite and protected authoring preflight:

```bash
python3 review.py task-tests 15df00eb9323 --phase after \
  --out ../checks/15df00eb9323-tests
python3 review.py run python3 \
  generators/15df00eb9323/workspace/parametric/preflight_compat.py \
  15df00eb9323 --out ../checks/15df00eb9323/qualification
```

The task-local preflight entry point only normalizes a catalog split stored as a single pair object into the one-element list expected by the packet preflight; all source binding, base replay, generation checks, worker execution, and protected-Racket receipt creation remain delegated to the official implementation.

The audit and preflight are finite reviewer evidence.  They do not grant source
approval, native acceptance, or training admission.
