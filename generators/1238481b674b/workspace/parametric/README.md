# Parametric triangle-render prototype

Status: **prototype / proposed**, not canonical approval.

This task-local prototype adds one bounded episode-level parameter while
preserving the original family's reasoning:

| Parameter | Values | Canonical/default |
|---|---|---|
| `render_mode` | `outline`, `solid` | `outline` |

Both settings infer the same axis-aligned square from four gray markers, locate
the absent corner, use that corner as the apex, preserve every gray clue, and
paint color 8 only over orange background. `outline` paints the two incident
square sides and opposite diagonal exactly as the canonical task does; `solid`
fills the triangle bounded by those same three edges.

The hidden mode is selected once from the episode seed (`even -> outline`,
`odd -> solid`) and is shared by four demonstrations and one query. The retained
episodes use medium inputs at sample indices `0,1,2,3` and query index `4`; every
pair distinguishes the two modes. Example labels are obtained by executing the
materialized Racket rule. The Python transform is an independent diagnostic
mirror only.

From the outer extracted packet directory, run:

```bash
python3 review.py run python3 \
  generators/1238481b674b/workspace/parametric/prototype.py \
  --out ../checks/parametric/render-mode-evidence.json \
  --write-public generators/1238481b674b/workspace/parametric/examples
```

Focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/1238481b674b/tests/test_parametric_render_mode.py -q
```

Outputs:

- `racket/outline.rkt`: byte-exact canonical source, normalized hash `cbabe9d66374`.
- `racket/solid.rkt`: complete proposed solid-fill source.
- `examples/outline_public.json` and `examples/solid_public.json`: labelled demos
  plus an unlabelled query, with no parameter or reference program.
- `WORK/checks/parametric/render-mode-evidence.json`: exact sources, hashes,
  executed pairs, alternative outputs, runtime identity, and limitations.

The production generator, catalog authority, rule hash, and frozen legacy test
fixture are intentionally unchanged.
