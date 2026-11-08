# Slide-direction prototype (proposed, not canonical)

This task-local prototype varies one hidden rule parameter once per complete
4-demonstration/1-query episode while preserving the original row-local block,
cyan-wall, and edge-fallback reasoning:

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `direction` | `left`, `right` | `left` |

`left` returns the canonical Racket program byte-for-byte.  `right` mirrors the
same operation: each contiguous green row block moves immediately before the
nearest cyan wall originally to its right, or to the right edge.  The rightward
Racket reduction processes block cells in reverse order so one-cell-overlap
moves do not erase a cell that was just written.

Inputs are generated separately from the production path but must pass the
selected generator's `self_check`.  Every retained demonstration and query is
constructed so the two directions disagree.  The script executes both exact
Racket programs through the included bridge, cross-checks independent Python
mirrors, emits public challenges without the hidden parameter/program/query
answer, and fails unless the requested seeds cover both settings.

From `WORK/` run (the retained evidence uses seeds listed in its summary):

```bash
python3 run_with_racket.py python3 generators/536de2f7591b/workspace/parametric/prototype.py \
  --seeds 0 2 --difficulty easy \
  --out-dir ../checks/parametric/slide-direction-v1
```

This is a proposed authoring variant only.  It does not modify or approve the
selected canonical rule, production sampler, or catalog entry, and its evidence
is bounded to the retained seeds and collision-free row-block input grammar.
