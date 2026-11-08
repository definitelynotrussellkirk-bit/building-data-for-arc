# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

`probe_mixed_orientation_gap.py` measures whether a solver can reuse the first
target's missing-corner orientation throughout each input. It scans generated
samples, checks the canonical train/query split, and retains a lawful mixed-
orientation witness.
