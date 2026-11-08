# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Connectivity repair and replay tools

`distribution_review/` retains the exact v2.1.0 baseline, independent component
and outline probes, two Racket-confirmed ambiguous natural lessons and a source-
bound before census. Its `final/` directory contains the matched v2.2.0 census,
64-input Racket calibration and `final_probe.py` for future reruns. That tool
requires `--generator` and a fresh `--out-dir`; it discovers the selected
generator's rival declarations dynamically and refuses to overwrite evidence.

`contract_review/` retains the 144-combination exact-axis probe, cyclic query
rotations, malformed-input regressions, before/after findings and initial
environment-failure evidence. Always pass a new `--out` to `probe.py`; its
historical default names the retained before report.

Run scripts through the packet's `run_with_racket.py` from the packet root.
Payload paths are relative to `repo/`. The return's DECISIONS.md provides exact
rerun commands, limitations and next priorities. Baseline and reviewed snapshots
are evidence; editing them never changes the selected generator.

## Independent morphology distribution probe

`morphology_distribution_probe.py` loads only a requested generator file and reconstructs components, bbox spans, normalized shapes, canonical-profile signatures, and lesson-window support from returned grids. It intentionally does not call producer-owned analysis, witness, rival, or output helpers.

From the packet's `repo/` directory:

```bash
PYTHONPATH=shared/runtime:shared/tools \
python3 generators/cc8c719680e6/workspace/morphology_distribution_probe.py \
  --generator generators/cc8c719680e6/generator.py \
  --seeds 250 \
  --out ../checks/morphology-distribution.json
```

Use it after morphology or schedule edits to compare normalized-shape support, bbox-span support, exact-input uniqueness, canonical joint profiles, and all sampled four-example windows. Its finite samples are a regression instrument, not a proof that no unmodeled shortcut exists.
