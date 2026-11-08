# Alignment-parametric connector prototype

**Status:** proposed, source-bound authoring artifact; not qualified, accepted, or admitted to training.

The episode-fixed `alignment` is either `diagonal` (the exact canonical default)
or `orthogonal`. Every scene contains two diagonal endpoint pairs and both a
horizontal and vertical pair, so the demonstrations distinguish the setting
without changing the source task's endpoint-pair discovery and line-tracing
reasoning. Demonstration counts are independently selectable from 2 through 6;
all episodes retain exactly four distinct controller-side queries. The last query
is a substantive 30×30 boundary case with five diagonal and four orthogonal
nonintersecting endpoint pairs; the fixed setting determines which long paths fill.

Only `public_turn(episode, i)` is solver-visible: demonstrations and one query
input, with no future inputs, answers, settings, program, ordinal total, or count
hint. `write_batch` publishes first-turn bytes only; later turns stay private.
Public identifiers hash those exact visible bytes through `reviewer_support`.

From the packet root:

```bash
python3 review.py run python3 generators/c7de5e8abc29/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/c7de5e8abc29/parametric-racket
```

The CLI executes every retained label through the protected bundled Racket
runtime and rejects teaching ambiguity, duplicate inputs, invalid counts, or
surviving named shortcuts. Python outputs are mirrors/proposals only.
