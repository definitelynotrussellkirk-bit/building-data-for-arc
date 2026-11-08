# Row-local cue-color reflection native candidate

Status: reviewer candidate; exact-source owner qualification and acceptance are
separate. The approved production generator and canonical rule are unchanged.

## Episode-fixed rule

| `copy_policy` | Behavior |
|---|---|
| `all` | Exact canonical rule: reflect every nonzero non-maroon source across that row's maroon anchor, retaining originals. |
| `nearest_color` | Find the source nearest that row's anchor, read its color, and reflect every source of that color in that row. |
| `farthest_color` | Find the farthest source, read its color, and reflect every source of that color in that row. |

Unselected sources, original source cells, anchors and rows without an anchor
remain unchanged. The selected color is discovered separately in each row;
it is not an episode parameter or a fixed color. Two different sources cannot
have equal distance from the same anchor in this grammar: one would occupy the
other's required empty reflected target.

`program()` returns the selected canonical source byte-for-byte for `all`.
The alternatives are complete `rule!` expressions. The adapter returns
Python claim labels; native qualification independently executes them through
protected Racket. No generation method starts a nested Racket audit.

The causal chain is row-local anchor/source discovery → nearest/farthest source
and its observed color → copying every matching source, including remote cells
on the other side. Later writes consume the discovered color. The witness
changes only the cue selector while preserving the copying code. This is an
input-derived selector followed by spatial transformation, not iterative-state
simulation or a measured claim about solver difficulty.

## Counts, grammar and coverage

- Seed is an exact integer in `0..2**63-1`. Counts are independently `2..6`
  demonstrations and `1..4` queries; defaults are three and four.
- Inputs and outputs share dimensions: height `4..30`, width `7..30`, integer
  colors `0..9`. Zero is background and nine is the row-local anchor.
- At least two rows have exactly one anchor and a source. At least one row has
  no anchor. Source cells occur on both sides across the scene. Each source's
  reflection is in bounds and empty in the original input. Those are grammar
  constraints, not hidden rejection of difficult labels.
- Generation builds all six demos and four queries before slicing. There are
  exactly ten constructive scene draws, with no rejection loop. The entire
  input bank is identical across settings and count requests.
- The first two scenes teach row-local axes, both copying directions, repeated
  selected colors, unanchored pass-through content, differing cue distances and
  different color-frequency ranks. Near and far members are interleaved so
  whole-color means and distance extents cannot substitute for individual cues.
  Counts vary between rows so frequency is not substituted for distance. A monochrome row supplies a setting-neutral
  case without making the lesson ambiguous.
- Demo profiles are `6×15`, `8×21`, `4×7`, `10×14`, `20×11`, and `30×30`.
  Queries are `5×9`, `12×22`, `30×17`, and `30×30`. These profiles are the sampled
  support; the grammar's dimension ranges are not a claim that every shape is
  sampled or that explicit size overrides exist.
- The largest demo/query have 24/25 anchored rows respectively, over 200 source
  cells, varying anchor columns, colored orphan rows, content in all quadrants,
  and boundary-reaching reflection pairs. This is substantial full-canvas work.
  Palettes, source spacing, anchor placement, orphan content and row/column flips
  vary with seed. Ninety-degree rotations are not a supported family symmetry.
- All ten inputs are distinct within an episode. Global cross-seed uniqueness is
  not guaranteed. Production remains at heights `4..10` and widths `7..15`; the
  native 30-side profiles and color-selection settings are not production overrides.

## Reproduce

From the extracted packet's outer directory after its runtime setup:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/71f7823f30a3/tests/test_native_family.py \
  generators/71f7823f30a3/tests/test_native_teaching_audit.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/71f7823f30a3/workspace/parametric/audit_native.py \
  --seeds 0 17 --demos 2 --out ../checks/71f7823f30a3/new-teaching.json

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  71f7823f30a3 --seed 0 --seed 17 --demos 6 --queries 4 \
  --out ../checks/71f7823f30a3/new-qualification --summary
```

Qualification deliberately uses six demonstrations to cover the complete bank;
ordinary generation defaults to three. The finite-rival teaching audit uses
only the first two. Rebuild the native inventory after source changes before
qualification. Rival survivors must be fixed from demonstrations alone; a
query answer cannot teach a later query. The report tests31 hypotheses, including a matching-policy positive control;
its30 alternatives are refuted by the first two demonstrations. Exact mean
comparisons use cross-multiplication in Racket. No universal identification
claim is made.

## One query per actor turn

The return's reusable exporter consumes native qualification evidence and
checks current source/runtime hashes without importing an adapter or evaluating
labels:

```bash
WORK/.venv/bin/python review.py run python3 ../checks/tools/export_qualified.py \
  --qualification ../checks/71f7823f30a3/qualification/qualification.json \
  --task-id 71f7823f30a3 --seed 0 \
  --out ../checks/71f7823f30a3/new-qualified-export
```

Expose only one current `actor/<visible-bytes-sha256>.json` file. It contains
visible demos and one query input, without its answer or any metadata. Keep
all private controllers, settings, programs, seeds, future inputs, manifests and
directory listings private. The first turn is identical whether one or four
controller queries are exported. This provides a checked projection for an
existing consumer, not a new turn controller or training loop.

Successful reviewer qualification/export does not confer owner acceptance or
training admission. The current causal interpretation and finite checks remain
bounded evidence for the exact source bytes.
