# Proposed cycle-direction prototype

This task-local prototype keeps the original framed-icon reasoning and changes
one episode-level semantic parameter:

- `cycle_direction = clockwise` (default): frame *i* receives the next
  clockwise frame's icon color. Its Racket text is byte-for-byte the canonical
  program.
- `cycle_direction = counterclockwise`: frame *i* receives the previous
  clockwise frame's icon color.

The input grammar is unchanged. Each episode chooses the direction once from
its deterministic seed, uses it for three demonstrations and one query, and
checks that every demonstration refutes the other setting. Outputs are executed
through the included protected Racket bridge. This is proposed evidence only;
it does not alter the canonical generator API, rule hash, or approval state.

From the outer extraction directory, run:

```bash
python3 review.py run python3 generators/a4863798ed70/workspace/parametric/prototype.py \
  --out ../checks/parametric/cycle-direction-v1 --seeds 0 1
```

Retained output includes exact `.rkt` files, public challenges with no hidden
parameter or query answer, private evidence, source hashes, rival checks, and
protected-runtime identity.
