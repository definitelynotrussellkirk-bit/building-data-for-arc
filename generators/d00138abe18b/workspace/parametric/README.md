# Row-edge/order parametric prototype

**Status:** proposed, source-bound authoring artifact; not qualified, accepted, or admitted to training.

The episode-fixed rule combines `read_side=left|right` with
`row_order=top_down|bottom_up`. The exact canonical left/top-down Racket program
is the default. Every generated nonempty row is a contiguous
`edge, interior, interior, edge` run with three colors: either edge differs from
the modal color, and repeated edge values plus nonmonotone row order defeat
modal, deduplication, and sorting shortcuts. Two demonstrations already identify
all four settings; 2–6 demonstrations are supported independently, and every
episode retains exactly four distinct controller-side queries. The last query
uses 24 rows across the full 30×30 canvas, including every outer boundary.

Only `public_turn(episode, i)` is solver-visible: demonstrations and one query
input, with no future inputs, answers, settings, program, ordinal total, or count
hint. `write_batch` publishes first-turn bytes only; later turns stay private.

From the packet root:

```bash
python3 review.py run python3 generators/d00138abe18b/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/d00138abe18b/parametric-racket
```

The CLI executes every retained label through the protected bundled Racket
runtime. Python outputs are mirrors/proposals only.
