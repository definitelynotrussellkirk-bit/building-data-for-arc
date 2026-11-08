# Workspace

`reference_probe.py` is the reusable independent oracle for this task. It provides:

- portable canonical-pair loading via `reviewer_support.find_root` and `canonical_pairs`;
- layout classification from pixels;
- the canonical column-priority output;
- row-priority, row-only, and column-only rival outputs.

It intentionally does not import private helpers from `generator.py`. Task tests import it through the snapshotted workspace, so it also verifies portable packet layouts. The selected implementation remains `../generator.py`; workspace files are never automatically selected as production generators.
