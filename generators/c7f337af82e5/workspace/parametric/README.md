# Control-mapping parametric prototype

**Status:** proposed, source-bound authoring artifact; not qualified, accepted, or admitted to training.

The episode-fixed `mapping` is `standard` (the exact canonical default:
control 1 selects hollow orange frames and control 2 selects solid orange
rectangles) or `reversed`. Every scene contains separated exact frames and
filled rectangles. The minimum two-example lesson uses controls 1 and 2, so it
teaches both branches and rejects control-ignoring, paint-all, and paint-none
shortcuts. Demonstration counts are selectable from 2 through 6, and every
episode retains four distinct controller-side queries. The final query uses five
large objects over all four boundaries of a 30×30 canvas; either shape class
spans all boundaries.

Only `public_turn(episode, i)` is solver-visible: demonstrations and one query
input, with no future inputs, answers, settings, program, ordinal total, or count
hint. `write_batch` publishes first-turn bytes only; later turns stay private.

From the packet root:

```bash
python3 review.py run python3 generators/c7f337af82e5/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/c7f337af82e5/parametric-racket
```

The CLI executes every retained label through the protected bundled Racket
runtime. Python outputs are mirrors/proposals only.
