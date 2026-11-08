# Disjoint five-rule union candidate

The adapter selects one private `rule` per episode: `whole_clockwise`
(the exact canonical default), `whole_counterclockwise`,
`largest_component_clockwise`, `largest_component_counterclockwise`, or
`marker_to_top_left`. The first four materialize the existing accepted programs
without byte changes. Legacy `source_mode`/`handedness` dictionaries remain
accepted by the adapter; native discovery uses the five-value `rule` enum.
The last rule rotates the whole square until its unique color-9 corner is at
top left, then applies the canonical clockwise quadrant arrangement. It comes
from review-789b5940d1ff7764. No object-source/normalization Cartesian variants
are introduced.

All choices share inputs: the retained native scene constructor supplies the
objects and distractors, with color 9 reserved for one non-target corner.
This marker does not change the largest component. The first two demos have
different marker corners, separating normalization from a fixed rotation.
Supported counts are 2–6 demos and 1–4 queries (default four); input sides reach
15 and output sides reach 30. The first two demos separate all five rules in
the focused sweep. This is finite evidence, not proof against arbitrary rules.

Focused reconciliation evidence: 50 seeds × five rules with matched inputs,
count prefixes, two-demo rule separation and bounds; protected Racket checked
100 labels at seeds 0 and 17. These checks are not native qualification or
acceptance. The owner must refresh the source-bound manifest, qualify and
accept the exact final bytes. Canonical production remains unchanged.

## Retained component/handedness implementation

The following describes the retained four-rule implementation reused by the union.

# Object selection and rotated-quadrant native candidate

Status: reviewer candidate; exact-source owner qualification and acceptance are
separate. Production `generator.py` and its canonical authority are unchanged.
The native adapter reuses the retained prototype's rotation/tiling operation.

## Episode-fixed rules

| Parameter | Values | Exact canonical default |
|---|---|---|
| `source_mode` | `whole`, `largest_component` | `whole` |
| `handedness` | `clockwise`, `counterclockwise` | `clockwise` |

`whole` uses the complete input square. `largest_component` discovers all
same-color, four-connected nonzero components, selects the unique largest by
occupied cells, and extracts **only that component** into its tight square
bounding box. Other objects inside that box become zero. The chosen square
then supplies the original, quarter-turn and half-turn quadrants. Clockwise
puts CW in top-right and CCW in bottom-left; counterclockwise swaps those two.
The top-left stays original and bottom-right stays rotated 180 degrees.

`program()` returns the selected canonical source byte-for-byte for the default.
The alternate programs are complete `rule!` expressions. Adapter outputs are
Python claims; the native worker independently executes every claimed label
through the packet's protected Racket runtime.

The causal dependency is component discovery/selection → object-only tight crop
→ quadrant tiling. The later geometry and colors depend on the discovered
object. A wrong-object intervention changes the final answer. This is geometric
composition with an input-derived intermediate, not an iterative-state claim.

## Native grammar and sampling

- Exact integer seed `0..2**63-1`; `2..6` demonstrations and `1..4` queries.
  Defaults are three demonstrations and four queries. Counts are independent.
- Shared input grammar: square side `2..15`, zero background, a unique largest
  four-connected same-color object with a square bbox and four distinct rotations.
  Alternate settings are total on that grammar. Tied maxima are excluded.
- Generated input sizes are `{2,3,9,11,12,15}`; `2..15` is the supported envelope,
  not a claim that every size is sampled or that explicit size overrides exist.
- A complete six-demo/four-query bank is built before prefix selection. Inputs
  and ordering are independent of settings and requested counts. Exactly ten
  constructive scenes are drawn; there is no rejection loop or silent truncation.
- The first two scenes use target sides five and four, with larger sparse boxes,
  greater total distractor-color mass, same-color diagonal contacts and a foreign
  object inside the target bbox. They teach object selection, connectivity,
  object-only extraction, variable crop size and quadrant handedness.
- The remaining demos include 2×2 and 3×3 anchors, a 9×9 scene and a 15×15 comb.
  Queries are 3×3, 9×9, 12×12 and 15×15. Palettes, rotations, positions, bar lengths
  and distractor placement vary. The 15×15 comb touches two full canvas edges
  and has multiple long branches; all four output quadrants contain real content.
- The source rule doubles each dimension. A 30×30 input would produce a 60×60
  canonical output, outside ARC's 30-side limit. This common grammar therefore
  exercises **30×30 outputs** from 15×15 inputs. Production still supports only
  input side two or three; native sizes/settings are not production overrides.
- Within an episode, all ten inputs are distinct. Cross-seed global uniqueness
  is not promised; tiny inputs can recur and downstream deduplication remains useful.

## Reproduce the source-bound checks

From the extracted packet's outer directory, after its runtime setup:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/196a7ec58bbc/tests/test_native_family.py \
  generators/196a7ec58bbc/tests/test_native_teaching_audit.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/196a7ec58bbc/workspace/parametric/audit_native.py \
  --seeds 0 17 --demos 2 --out ../checks/196a7ec58bbc/new-teaching.json

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  196a7ec58bbc --seed 0 --seed 17 --demos 6 --queries 4 \
  --out ../checks/196a7ec58bbc/new-qualification --summary
```

The qualification count six deliberately covers the entire bank, while ordinary
sampling defaults to three and the teaching audit uses only the first two.
The current inventory must be rebuilt after source changes before qualification.
The retained audit tests twelve explicit rivals, including a fixed-five-side
crop that exposed and repaired the original two-demo teaching hole. Survivors
are decided from demonstrations before any query labels are considered. A
finite no-finding result is not universal rule identification.

## One current query per actor file

The return's reusable `checks/tools/export_qualified.py` reads native
qualification/execution evidence without importing adapters or re-executing
programs. It verifies current source/runtime hashes and emits private controllers
plus separate one-query actor files:

```bash
WORK/.venv/bin/python review.py run python3 ../checks/tools/export_qualified.py \
  --qualification ../checks/196a7ec58bbc/qualification/qualification.json \
  --task-id 196a7ec58bbc --seed 0 \
  --out ../checks/196a7ec58bbc/new-qualified-export
```

Expose only the current `actor/<visible-bytes-sha256>.json`. Each has the visible
demonstrations and exactly one masked query. Keep the manifest, directory listing,
private controller, settings, seed, programs, future inputs and answers private.
The first actor file is identical when exporting one or four controller queries.
This verifies a projection for an existing consumer; it implements no turn
controller or training loop and claims no training admission.

## Retained earlier prototype

`prototype.py`, `verify.py`, `programs/` and historical `episodes/` remain as
prior authoring evidence. Their older count limits and all-query public files
are not this native API or its actor boundary. In particular, the historical
v1 setting-named public files must not be exposed as native actor turns.
