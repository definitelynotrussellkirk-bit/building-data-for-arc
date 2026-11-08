# Workspace — fc41c9b3a565

The selected implementation is `../generator.py`. Workspace tools do not alter
selection.

## `semantic_probe.py`

A cheap, source-bound authoring check that reports:

- self-check failures and exact scene-profile counts by difficulty;
- strict linked-canonical hit counts;
- all declared semantic witness firing rates;
- disagreement rates for every declared rival;
- four-demonstration production identifiability;
- every query rotation in the same five-pair window.

Run from the packet's `repo` directory through the verified runtime:

```bash
python3 ../run_with_racket.py python3 \
  generators/fc41c9b3a565/workspace/semantic_probe.py \
  --seeds 1301,1302 --per-band 20 --lesson-starts 12 \
  --out ../checks/task-semantic-probe.json
```

The probe uses the Python rule mirror for speed. It complements rather than
replaces `rule_smoke`, `racket_lint`, and `authority_sync`.
