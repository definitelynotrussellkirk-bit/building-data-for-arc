# Proposed quarter-turn parameter prototype

This task-local prototype keeps the canonical whole-grid rotation family and adds one episode-fixed parameter:

- `quarter_turns = 1`: rotate 90 degrees clockwise.
- `quarter_turns = 2`: rotate 180 degrees; this is loaded byte-for-byte from the canonical ledger and remains the default.
- `quarter_turns = 3`: rotate 90 degrees counterclockwise.

The setting is chosen once per episode. Demonstrations and queries use independent counts, every retained input distinguishes all three declared settings, and each query is checked using demonstrations only before its private answer is used. Labels are executed by the protected Racket bridge and cross-checked against an independent Python rotation.

From the packet's outer directory, generate paired evidence for all settings with three demonstrations and four distinct queries:

```sh
python3 review.py run python3 generators/88b8e6aaa49d/workspace/parametric/prototype.py \
  --seed 17 --quarter-turns all --demos 3 --queries 4 \
  --out ../checks/parametric/quarter-turns-v1
```

Run the focused checks:

```sh
python3 review.py run python3 -m pytest \
  generators/88b8e6aaa49d/tests/test_parametric_rotation.py -q
```

`adapter.py` and `promotion.json` are a narrow promotion-shaped interface for owner review. This directory is proposed evidence only: it does not modify the canonical generator, refresh its approval, or admit any variant to training. Identifiability is established only within the declared `{1,2,3}` quarter-turn family, not against arbitrary programs.
