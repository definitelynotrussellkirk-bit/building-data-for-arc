# Workspace

`room_graph_probe.py` is a bounded source-bound replay for the selected
`../generator.py`. From the repository root:

```sh
PYTHONPATH=shared/runtime python3 \
  generators/6b694a414d96/workspace/room_graph_probe.py \
  --seeds-per-band 80 --output ../checks/6b694a414d96-room-graph-probe.json
```

It checks all labeled canonical pairs, every three-profile lesson window in the
sample, generated validation/parity, the canonical-shortcut declaration,
second-hop witnesses, and finite-rival lesson identifiability. It records the
selected source SHA-256 and exits nonzero on any finding. It is a finite replay
tool, not a universal proof or a replacement for Racket rule-smoke.
