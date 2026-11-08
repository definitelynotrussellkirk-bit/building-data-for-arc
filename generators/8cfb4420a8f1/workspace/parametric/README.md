# Parametric erase-scope prototype

This is an **isolated proposed prototype**, not a change to the selected
canonical generator or its pinned Racket authority.

## Parameter

`erase_scope` is selected exactly once per episode from the deterministic episode
seed.

- `body_only` — default/original setting. Keep the unique top-row marker and erase
  matching-colour cells below row 0.
- `all_occurrences` — proposed alternative. Erase every cell of the selected
  colour, including the top marker.

Both settings retain the same core reasoning: infer a selected colour from the
unique top-row marker and remove that colour. The input grammar requires one
nonzero top marker and at least one matching body cell. Every retained episode
contains three demonstrations and one query; the demonstrations distinguish the
settings because the top marker survives only under `body_only`.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/8cfb4420a8f1/workspace/parametric/build_prototype.py \
  --out-dir ../checks/parametric/erase-scope-v1
```

The builder refuses to overwrite evidence. It writes redacted public challenges,
full private evidence, exact Racket text and hashes, source hashes, query answers,
and a summary under `WORK/checks/parametric/erase-scope-v1/`.

`prototype.py` contains a Python mirror for focused tests, but the retained labels
are produced by executing the materialized Racket programs through the included
Racket bridge. Public challenge JSON omits the seed, hidden parameter, Racket
source, and query answer.
