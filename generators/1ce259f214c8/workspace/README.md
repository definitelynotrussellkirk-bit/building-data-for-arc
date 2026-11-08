# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

## Reusable probes

### `shortcut_probe.py`

Measures the original canonical-compatible rival: occupancy XOR with the complete output border forced to zero. It checks canonical fit, per-band counterexamples, lesson survival, and schedule behavior.

### `regional_shortcut_probe.py`

Independently constructs 70 stronger competitors. Each agrees with XOR except on one of ten canonical-empty regions—the border, an edge, the corner set, or an individual corner—where it substitutes one of seven operations: zero, OR, AND, left copy, right copy, left-minus-right, or right-minus-left.

The probe reports canonical fit, regional relation coverage, survival across a configurable number of demonstrations, and dangerous query disagreements. By default it reads `EXAMPLES_NEEDED` from the prepared runtime. Point it at immutable before and after runtimes to make a deterministic comparison.
