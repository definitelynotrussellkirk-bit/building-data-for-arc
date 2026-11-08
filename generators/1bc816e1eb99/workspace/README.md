# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Reusable probes

- `reference_probe.py` provides an independent component/hole oracle and batched Racket replay.
- `curriculum_probe.py` audits linked lessons, declared rivals, uniqueness, validation, determinism, and sampled Racket parity.
- `scalar_boundary_probe.py` audits literal-integer `seed`/`sample_index` handling at both public entry points. It creates its own output directory and exits nonzero on accepted malformed scalars or rejected valid controls.

Example from `WORK/repo`:

```bash
python3 generators/1bc816e1eb99/workspace/scalar_boundary_probe.py \
  --generator generators/1bc816e1eb99/generator.py \
  --out ../checks/1bc816e1eb99-scalar-boundary.json
```
