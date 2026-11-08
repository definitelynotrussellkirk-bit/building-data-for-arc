# Proposed `gallery_gap` rule parameter

This isolated prototype varies one executed rule choice while preserving the
pairwise-union-gallery family. The setting is chosen once from the episode seed
and reused for all four demonstrations and the query.

| value | meaning | status |
|---|---|---|
| `0` | no background separator between 3x3 panels | proposed alternative |
| `1` | one background row/column between panels | canonical default |
| `2` | two background rows/columns between panels | proposed alternative |

No input constraint changes with this parameter. Every lawful three-shape input
produces output dimensions `9 + 2*gallery_gap` in each direction, so any labeled
demonstration distinguishes all three settings before the query.

From the packet root, execute all complete Racket programs and rebuild the
source-bound evidence with:

```sh
python3 review.py run python3 \
  generators/27b865c5f43a/workspace/parametric/gallery_gap.py \
  --out-dir ../checks/parametric/gallery-gap-v1
```

The command writes one full evidence episode and one answer-free public
challenge for each setting. Retained `racket/gap_*.rkt` files are complete
materialized programs; `gap_1.rkt` must retain normalized hash
`de4d9d03f710`.

This is a **proposed prototype**, not a selected generator change, a canonical
rule edit, or an approved production interface. It is intentionally modest:
the parameter is clear and testable, but it may be too superficial to improve
reasoning value because it changes spacing rather than the union operation.
