# Workspace

The selected implementation is `../generator.py`; workspace files are retained authoring aids and are never selected automatically.

- `generator.before.py` is the packet baseline (`2.1.0`) kept for direct comparison.
- `probe_bbox_curriculum.py` is a portable source-bound regression probe. It reads canonical pairs through `reviewer_support.find_root`, discovers declared shortcut/competitor functions from the sibling generator, and checks every contiguous three-demonstration window.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/5a70e1b62a50/workspace/probe_bbox_curriculum.py \
  --seed-count 8 --samples-per-seed 16 --out ../checks/bbox-curriculum-probe.json
```

The probe's generated labels use the explicitly diagnostic Python mirror. Use the shared semantic gate or lesson census for Racket-authority-labelled evidence.
