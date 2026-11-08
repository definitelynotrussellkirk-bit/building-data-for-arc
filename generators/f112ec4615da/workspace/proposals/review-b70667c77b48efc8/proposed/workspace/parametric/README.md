# Proposed overlay-priority parameter (prototype only)

This original ARC family supports one small episode-level rule parameter while
preserving its core reasoning structure:

- `overlay_priority = "tr_bl_br_tl"` — **canonical/default**, highest priority
  first: top-right, bottom-left, bottom-right, top-left.
- `overlay_priority = "tl_br_bl_tr"` — proposed alternative, the exact reverse
  role order.

Both settings split an even input into four aligned quadrants, treat zero as
transparent, compare the four cells at each local coordinate, and emit a
half-sized output. Only the role priority changes. The parameter is selected
exactly once from the episode seed and is shared by two labelled demonstrations
and one query. Every retained demonstration distinguishes the two settings.

The production generator and canonical Racket authority remain fixed to
`tr_bl_br_tl`. This directory is isolated proposal evidence, not production or
training approval.

From the packet extraction directory, execute both exact retained Racket
programs and write private/public evidence with:

```bash
python3 review.py run python3 \
  generators/f112ec4615da/workspace/parametric/prototype.py \
  --seed 19 \
  --out ../checks/parametric/overlay-priority-seed19.json \
  --write-public generators/f112ec4615da/workspace/parametric/examples
```

The command materializes `rules/priority_tr_bl_br_tl.rkt` and
`rules/priority_tl_br_bl_tr.rkt`, executes each on every pair, checks labels
against the independent Python mirror, and checks every demonstration against
the other setting. Public JSON retains labelled demonstrations but omits the
hidden parameter and query answer.
