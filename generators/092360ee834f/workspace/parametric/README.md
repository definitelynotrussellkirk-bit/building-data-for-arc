# Parametric family: ordered area match

The row-0 count still produces the target area `k`. The body is filtered to
4-connected green components of area `k`; the episode-fixed `match_order`
selects either the first or last match in row-major scan order.

- `first` is the exact canonical Racket program and the promotion default.
- `last` reverses the canonical object list before the same `find-first` step.

Every supported lesson has 2–6 demonstrations and four controller-side queries
(the adapter also supports query prefixes 1–8). Inputs are matched across
settings. Scenes vary `k`, object geometry, match locations, green area decoys,
same-area non-green objects, body blue cells, and a 4-vs-8-connectivity trap.
The fourth query is a substantive 30×30 scene. Public projection is delegated
to the shared exporter; settings, programs, presentation order, future inputs,
and query answers remain private.

Sequential dependency: **A** counts row-0 blue cells; the intermediate is the
input-dependent integer `k`; **B** filters green body components by area `k`
and only then applies the episode's first/last order. A wrong `k` changes the
eligible component set and therefore the final output.

## Reproduce a protected-Racket sample

From `WORK/repo`:

```bash
PYTHONPATH=src:shared/runtime python3 ../run_with_racket.py \
  python3 generators/092360ee834f/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 2 --queries 4 \
  --out var/092360ee834f-parametric-sample
```

The command refuses an existing output directory and writes public challenge
bytes separately from private settings, programs, query answers, certificates,
and protected-runtime identity.
