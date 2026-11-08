# Native bbox and diagonal-gap completion

This task-local family preserves the approved `68a312813b77` generator and its
exact canonical program. One hidden episode-level parameter chooses the region
to complete:

| `completion` | Executed rule |
|---|---|
| `bbox` (default) | Fill zero cells in each original same-color 8-connected object's axis-aligned bounding box with 7. |
| `diagonal_gaps` | Make those same bbox fills, then also fill pairwise diagonal overlap gaps derived from the original objects. |

For each object compute projected coordinates `u = row + column` and
`v = row - column`. An ordered pair A, B contributes a bridge when its `u`
extents are disjoint, `A.umax < B.umin`, and its `v` intervals overlap. Paint
zero cells satisfying:

```text
A.umax < row + column < B.umin
max(A.vmin, B.vmin) <= row - column <= min(A.vmax, B.vmax)
```

Pairing is color-agnostic; the objects themselves are monochrome components.
All eligible pairs contribute, including non-nearest pairs. Every original
nonzero cell is preserved. Components and projected extents come from the
original input, before any painting. Both settings use literal background 0
and fill color 7; generated input objects do not use 7.

## Why the stages depend on one another

Stage A extracts original objects and derives their projected extents and
pair-specific overlap intervals. Stage B paints the corresponding regions.
The fill limits depend on whole-object geometry, including interval values
between sampled pixel projections. Replacing intersection with union, scanning
only literally occupied diagonals, or extracting objects again after painting
produces different rules. A protected counterfactual witness accompanies the
native qualification in the review return.

## Pinned public-evaluation inspiration

The assignment pins public-evaluation task `7666fa5d`, challenge SHA-256
`1b19ed6f202f6b9addff88314b0697b2752f581a55994c0339948f7cf3f8cd6d`.
Its supplied demonstrations motivate deriving overlap intervals from diagonal
objects before completing a region. The retained `checks/68a312813b77/source_probe.py`
executes that candidate on both supplied demonstrations, using background 8,
fill color 2, and no own-object bbox stage.

The new family transfers that interval-overlap mechanism while retaining this
MAIN task's bbox completion and 0/7 colors. It does not claim equivalence to the
focus task or verified lineage. No focus test answer is generated. Inspiration
metadata remains private, `relationship_verified=false`, and training admission
remains false; protected family partition policy is unchanged.

## Run and verify

Use the Python 3.12+ interpreter that passed `review.py python-check`. From the
outer packet directory, after `review.py setup`:

```bash
python3 review.py run python3 -m pytest \
  generators/68a312813b77/tests/test_native_adapter.py \
  generators/68a312813b77/tests/test_native_family.py \
  generators/68a312813b77/tests/test_native_export.py \
  generators/68a312813b77/tests/test_native_audit.py -q

python3 review.py run python3 \
  generators/68a312813b77/workspace/parametric/audit_native.py \
  --out ../checks/68a312813b77/audit-replay

python3 review.py run python3 \
  generators/68a312813b77/workspace/parametric/make_examples.py \
  --seed 0 --demos 3 --queries 4 \
  --out ../checks/68a312813b77/examples-replay

python3 review.py run python3 -m arcpuzzles parametric qualify 68a312813b77 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/68a312813b77/qualification-replay --summary
```

Use fresh output paths. Qualification requires the current native source and
evidence inventory; after source changes, regenerate it through
`arcpuzzles parametric manifest` before qualifying again. The manifest inventory
does not itself execute checks or grant acceptance.

`adapter.py` loads the adjacent `prototype.py`. Generation returns deterministic
claim labels and complete Racket source without starting nested evaluators.
The native worker, finite audit, and example builder independently execute the
programs through protected Racket. The audit fits each alternative to
demonstrations before inspecting its query predictions; errors fail the check,
and equivalent survivors are reported honestly.

## Counts, scenes, and model-visible turns

Demo and query counts are independent: **2–6 demonstrations and 1–4 queries**,
defaulting to three and four. The first two demonstrations include active
partial overlap, inactive disjoint projections, thick objects, and multiple
pair relationships. Seeds vary geometry and colors independently of the hidden
setting. Four queries include substantive 30×30 content; all inputs within an
episode are distinct. Requesting one query preserves the same demos and first
query as requesting four.

`export.public_turn(episode, query_index)` returns only demonstrations and one
current query input. Give an actor that object, after the preceding answer,
without a total-count or final-turn hint. `make_examples.py` writes:

| Path | Contents and consumer |
|---|---|
| `turns/<sha256>.json` | Actor payload: demos and exactly one query input. |
| `public/<sha256>.json` | Controller payload: demos and all query inputs. |
| `private/metadata.jsonl` | Full episodes, answers, programs, settings, certificates, and ordered turn IDs. |

IDs hash exact canonical visible bytes. Private fields and future queries
cannot influence the first-turn payload. The transport writer rejects duplicate
visible payloads before publication and refuses existing destinations. The
transport module does not authenticate labels; use protected execution first.

## Scope

Production remains v2.3.0 with SHA-256
`8e09a3589eab5c5413b7e2d6fb88f67f962dc6240ccdef01af31901f78419007`.
The canonical default is exactly
`(rule! (lambda (g) (fill-object-bboxes-8 g 7)))`.
The native sampler's larger scenes and relational completion are a separate
opt-in family, not changes to production dimension or placement controls.

Native qualification and finite audits cover the exercised settings, seeds,
rivals, and count boundaries. They do not prove universal identifiability,
universal sampler correctness, or measured learning benefit. Owner qualification
and acceptance of the integrated exact source remain required; no training
admission is asserted by this prototype or its example exports.
