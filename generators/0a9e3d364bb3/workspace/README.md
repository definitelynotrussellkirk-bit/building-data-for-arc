# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

`probe_rotation_curriculum.py` is a portable, task-local regression probe. It dynamically loads the selected generator, verifies that every declared canonical shortcut fits all canonical pairs, then checks all query positions for every cyclic schedule start across configurable seeds and all three difficulty bands. It writes compact JSON and exits nonzero on any ambiguity or coverage failure.

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/0a9e3d364bb3/workspace/probe_rotation_curriculum.py \
  --seeds 16 --out ../checks/rotation-probe-final.json
```
