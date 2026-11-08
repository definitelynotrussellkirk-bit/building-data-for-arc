# Rectangle outlines and visible-border selection

This is a separate native parametric candidate for `8d2cfdfec79c`. The selected
production generator and canonical Racket authority remain unchanged. Native
qualification is reviewer evidence; the owner must accept the exact integrated
source before the opt-in accepted-parameter API may use it. No training admission
or allocation change is made here.

## Rule and supported requests

| `mode` | Transformation |
|---|---|
| `outline` (default) | Exact, byte-identical selected canonical Racket program: draw each color's rectangle border in row-major first-appearance order. Later borders overwrite earlier ones. |
| `fill_most_visible` | Draw those same borders; count the surviving pixels of each color; select the greatest count, with ties going to first appearance; fill only zero cells strictly inside that color's original bounding box. |

Each input contains 2–6 nonzero colors, each occurring exactly twice at opposite
corners. The separate parametric grammar supports 8–30 rows and 10–30 columns.
The canonical production sampler retains its existing 8–13 by 10–14 limits.
Inputs include crossing, nested and disjoint boxes, thin rectangles, boundary
contacts, and both diagonal orientations. Every four-query request includes a
30×30 interacting scene spanning the canvas; other queries cover canonical and
larger rectangular sizes. This is meaningful geometry, not empty padding.

`generate(seed, settings, demos=3, queries=4)` supports 2–6 demonstrations and
1–4 queries independently. Seeds are exact integers in `0..2**63-1`; booleans
and coercible scalar values are rejected. Settings name exactly `mode`. Every
demo/query input is distinct. Separate deterministic input streams omit the
mode and the requested counts, so matched seeds use the same inputs across
settings and requesting future queries does not alter the first one.

Raw adapter outputs contain Python label claims. The native worker independently
executes every admitted label using protected Racket; raw calls alone do not
verify labels or approve a source.

## Why the intermediate matters

**A:** render all outlines with overwrite semantics. **Intermediate:** the
surviving count by color and the selected color. **B:** fill zero interior cells
of the selected color's original box. A rectangle with the greatest original
perimeter can lose enough pixels to later borders that another rectangle wins.
The causal witness substitutes original perimeter for surviving count and shows
a different protected-Racket final output.

The first two demonstrations are constructive teaching anchors:

1. A large outer rectangle loses border pixels to a narrower rectangle. A third,
   smaller fillable rectangle crosses the winner, so preserving other borders
   and using visible counts both affect the answer.
2. A thin rectangle and a fillable rectangle tie at 12 visible pixels. The thin
   one appears first and wins, so nothing is filled. A clue is overwritten and
   a third thin rectangle remains visible. This teaches first-appearance ties
   and that rectangles with no interior must still participate in selection.

An earlier pair of anchors admitted overwrite-interior, smallest-fillable, and
thin-exclusion shortcuts. The retained before counterexample and repaired
Racket cases explain why these anchors were strengthened without adding demos.
`audit.py` fits its declared rivals to demonstrations only, then checks each of
the four queries independently. Finite rivals and sampled seeds do not establish
uniqueness against every possible rule or measured learning benefit.

## Reusable checks and projection

From the outer packet folder, with its checked Python environment active:

```bash
python3 review.py run python3 -m pytest \
  generators/8d2cfdfec79c/tests/test_parametric.py \
  generators/8d2cfdfec79c/tests/test_parametric_public_export.py -q

python3 review.py run python3 \
  generators/8d2cfdfec79c/workspace/parametric/audit.py \
  --out ../checks/8d2cfdfec79c/fresh-audit
```

The audit uses 18 native jobs (seeds 0, 17, 33; demos 2, 3, 6; both settings;
four queries), 29 finite rivals, explicit minimum/maximum rectangular boundary
cases, and five Racket counterfactuals. Outputs must be fresh directories. It
retains exact source hashes, protected runtime identity, small private examples,
and first-turn public files. A nonzero exit or a failed report must be inspected.

`public_export.public_turn(episode, query_index=0)` projects exactly one query
input plus demonstrations. It excludes settings, seeds, programs, answers,
future inputs and total-count hints. The existing consumer controls reveal
order; this helper is not a turn controller. `write_public_turns` validates the
whole batch before creating a fresh directory, rejects duplicate visible
payloads, sorts content IDs, and hashes the exact visible bytes. Give a solver
only its selected public projection; `examples.private.json` contains all four
controller-side queries and their labels.

## Native promotion handoff

After scoped evidence is current, build the inventory with `arcpuzzles
parametric manifest`, including the two task-local test files. The supplied
`evidence/manifest.json` binds source and compact evidence; it grants no approval.
The reviewer qualification lives at
`WORK/checks/8d2cfdfec79c/qualification/qualification.json`, beside `execution.json`.

After integrating the exact delta, the owner uses the existing API:

```bash
arcpuzzles parametric qualify 8d2cfdfec79c --seed 0 --seed 17 \
  --demos 3 --queries 4 --out var/review/qualification-visible-borders --summary
arcpuzzles parametric accept 8d2cfdfec79c \
  --qualification var/review/qualification-visible-borders/qualification.json \
  --reason 'Reviewed visible-border dependency, teaching repair and source-bound evidence'
```

The owner's intake also replays the supplied sequential-dependency witness.
Source drift requires fresh inventory/qualification; a reviewer `ready` record
is not native acceptance.
