# Border projection-span prototype

Status: **proposed prototype**, separate from the selected canonical generator
and not approved for production.

The bounded hidden parameter is `projection_span`:

- `1` — canonical/default: every color-1 marker paints the one adjacent cell
  toward the matching colored border.
- `2` — proposed variant: it paints a contiguous two-cell ray in the same
  direction with the same border color.

The original reasoning pattern is unchanged: detect the solid opposite-border
orientation, classify each marker by its half of that axis, choose the matching
border and direction, and copy that border color. Only the final small count
changes. The value is selected once from the deterministic episode seed and is
held fixed across three demonstrations and one query.

## Input contract

Prototype inputs keep exactly one pair of distinct, nonzero, non-1 solid
opposite borders and color-1 markers in both axis halves. Every marker has two
disjoint background cells toward its matching border. That two-cell clearance is
the only parameter-dependent domain restriction and is stricter than the
canonical span-1 domain. The sampler alternates horizontal and vertical borders,
keeps odd-axis tie cases, varies dimensions/colors/layouts, and uses identical
inputs when the hidden span changes.

## Execute and reproduce

From the outer extracted packet:

```bash
python3 review.py run python3 \
  generators/b19deac47327/workspace/parametric/prototype.py \
  --out ../checks/parametric/projection-span-evidence.json \
  --write-public generators/b19deac47327/workspace/parametric/examples
```

Run the focused portable tests:

```bash
python3 review.py run python3 -m pytest \
  generators/b19deac47327/tests/test_parametric_projection_span.py -q
```

`racket/span-1.rkt` is byte-for-byte the canonical ledger program.
`racket/span-2.rkt` is the complete proposed variant. The evidence command
executes both programs through `RacketBridge`, checks all labelled canonical
pairs under span 1, records a complete episode for each setting, compares the
declared rival on every pair, and checks all four possible query rotations.
Public challenge files expose labelled demonstrations and query inputs only;
they omit the parameter, Racket source, and query answers.

The `_lesson_gate` helper inside `prototype.py` is a reusable pairwise hidden-rule
check for future authoring: it fails a lesson when the demonstrations do not
refute the rival before a query requires the distinction. Its evidence is
bounded to the declared `{1, 2}` settings and retained seeds, not arbitrary
hypotheses or production admission.
