# Proposed episode-level `partition_axis` parameter

This is a **prototype**, not part of the selected canonical generator or its
approval path. The transformation keeps the original reasoning pattern: two
colored interior dots each seed a rectangular frame in one half of the canvas.
Only the partition axis changes, once per episode.

| value | dot ordering and regions | status |
|---|---|---|
| `horizontal` | sort by row; upper/lower dots frame the upper/lower halves | canonical/default |
| `vertical` | sort by column; left/right dots frame the left/right halves | proposed alternative |

Prototype inputs contain exactly two distinct interior dots, with one dot in
each horizontal half and one in each vertical half. Thus the same input is
lawful under both settings and gives a direct declared-rival comparison. Each
episode has three labelled demonstrations and one query. The parameter is fixed
for the entire episode; public challenges omit the parameter, Racket source,
and query answer.

From the packet root, verify both settings with the protected Racket runtime:

```bash
python3 review.py run python3 \
  generators/df3c6021b715/workspace/parametric/verify.py \
  --seed 20261019 \
  --out ../checks/parametric/axis-report.json \
  --artifact-dir generators/df3c6021b715/workspace/parametric/materialized
```

The verifier checks that the horizontal program matches the canonical program's
normalized hash; that the retained `rules/horizontal.rkt` and
`rules/vertical.rkt` files match the emitted programs; and that Racket, the
Python authoring mirror, and every retained episode output agree. It also runs
the alternative setting on the exact same inputs and requires every
demonstration and query to disagree.

The retained seed produced 8/8 Racket-checked pairs, 6/6 distinguishing
training pairs, and 2/2 distinguishing queries. This finite two-setting probe
does not approve a production parametric API, establish uniqueness against
undeclared rules, or test inputs outside the deliberately dual-lawful domain.
