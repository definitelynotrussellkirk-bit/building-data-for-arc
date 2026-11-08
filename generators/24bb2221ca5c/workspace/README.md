# Workspace

The selected implementation is `../generator.py`. This directory retains auditable probes and historical drafts; workspace files are never selected automatically.

- `generator_v2_1_0_baseline.py` — imported baseline for direct comparison.
- `profile_probe.py` — samples complete three-example windows and records profiles, overrides, topology counts, witnesses, and rival counterexamples.
- `verify_shortcut_counterexample.py` — real-Racket side-gap versus bbox-fill reproducer.
- `verify_topology_counterexamples.py` — real-Racket multi-hole and same-color-component reproducer.
- `verify_connectivity_shape_counterexamples.py` — real-Racket 4-vs-8 background connectivity and nonrectangular-hole reproducer.

Run the focused tests before trusting any probe because the scripts import the selected generator contract.
