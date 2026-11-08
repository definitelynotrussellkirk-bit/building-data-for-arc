# Proposed sort-order rule parameter

This task-local prototype keeps the original `ee64b9b0fe20` reasoning chain and
varies one executed rule parameter once per episode:

| Parameter | Values | Canonical/default |
|---|---|---|
| `sort_order` | `ascending`, `descending` | `ascending` |

Both settings infer the nonzero modal background, find monochromatic
four-connected objects, discard any component whose bounding box spans the whole
canvas, sort by **cell count**, then bottom-align and left-pack bounding boxes.
Only the comparison direction changes. The ascending program is byte-for-byte the
canonical Racket authority; the descending program changes exactly the `<`
object-size comparator to `>`.

Inputs stay in the canonical generator's documented domain: at least two
non-frame objects with distinct cell counts and packable total widths. The
prototype retains only pairs for which reversing the order changes the complete
output. Thus each three-demonstration episode distinguishes the chosen setting
from its parameter rival before the query.

## Run

After `python3 review.py setup`, from the extracted packet root:

```sh
python3 review.py run python3 \
  generators/ee64b9b0fe20/workspace/parametric/sort_order_prototype.py \
  --out ../checks/parametric/sort-order
```

The command materializes one complete ascending episode and one complete
descending episode, executes both the chosen and rival Racket programs for every
pair, and writes:

- `summary.json` — source/program hashes, seeds, commands, and parity results;
- `ascending/` and `descending/episode_private.json` — hidden setting, programs,
  query answers, rival answers, and Racket verification;
- `ascending/` and `descending/challenge_public.json` — demonstrations and query
  inputs only, with no hidden parameter, reference code, rival labels, or query
  answers;
- one exact `program.rkt` per setting.

This is a **proposed task-local prototype**, not a production API, canonical-rule
change, approval, or training-admission claim. The evidence covers two bounded
settings and finite episodes. Cell-count ties, arbitrary large objects, and other
packing directions remain outside this prototype.

Public export identifiers are hashes of visible challenge content. Deliver only `public/`; private settings, programs and answers remain separate. Original reviewer source and gallery are preserved under `evidence/reviewer-original/`.
