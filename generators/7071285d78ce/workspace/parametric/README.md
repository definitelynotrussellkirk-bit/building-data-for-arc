# Transpose each object, then select components

This native prototype has one episode parameter, `selection`, with three values:

| Setting | Result |
|---|---|
| `all` | The exact selected canonical Racket program: transpose every source object locally and retain the entire result. |
| `largest` | Render that same intermediate grid, discover its same-color four-connected components afresh, and retain every component tied for greatest occupied-cell count. |
| `smallest` | Render the intermediate grid and retain every component tied for least occupied-cell count. |

An object's bbox top-left `(r0, c0)` remains its anchor. Its cell `(r, c)` moves
to `(r0 + c - c0, c0 + r - r0)`. The intermediate and final grids have the input
dimensions and a zero background. Rendering starts from a blank canvas; source
cells are not retained automatically. Selected cells keep their original colors.
Area means occupied cells, not bounding-box area or total cells of a color.

## Why the second step depends on the first

Separated source objects of the same color can become adjacent after their
local transposes. The first demonstration includes source areas `2, 3, 4, 4`:
the two smaller pieces become one area-5 component, leaving intermediate areas
`5, 4, 4`. Selecting largest or smallest source objects before transposition
therefore gives a different answer from the intended order. The selector needs
the rendered component structure, not just source sizes.

The next demonstration has intermediate areas `8, 6, 8, 6`, with ties at both
extrema, unlike-color contact, and nonidentity six-cell square-bbox shapes.
The third adds a real area-10 merger, tied singletons, and a destination that
crosses another object's original footprint. Destination/source intersections
are lawful because rendering starts blank; destination/destination collisions
are rejected.

Both stages use same-color **four-connectivity**. Diagonal contact alone does
not join components, and orthogonal contact between different colors does not
join them. The prelude's `objects-multicolor` helper instead uses color-blind
eight-connectivity. The audit's color-blind-four rival explicitly binarizes the
intermediate and calls `objects`, so that rival isolates the color distinction.

## Native API and admitted inputs

`adapter.program(settings)` returns complete Racket source.
`adapter.generate(seed, settings=None, demos=3, queries=4)` returns private
input/output pairs and `program_solution`. Explicit settings must be a dict
with exactly the `selection` key and one of the three supported string values.
When settings are omitted, `seed % 3` chooses from that ordered list.

Seeds are exact integers in `0..2**63-1`; demonstration counts are exact
integers in `3..6`, and query counts in `1..4`. The two counts are independent.
Booleans, floats, missing or extra setting keys, and unsupported values are
rejected. The full six-demonstration/four-query bank is constructed before
slicing, using local SHA-derived RNG streams independent of settings. Changing
a requested count preserves the corresponding prefix and the other bank.

The validator admits rectangular grids with each dimension in `8..30`, exact
integer colors `0..9`, background zero, and `2..24` source components. Nonzero
colors may repeat across components. Connected shapes may be rectangular,
square, transpose identities, lines, or singletons. Distinct source components
must have orthogonal clearance even when their colors differ. Every transformed
cell must fit, and different source objects' destination sets must be disjoint.
These are prototype extensions: unchanged production remains `8..14`, `2..4`
distinct-color nonrectangular objects of three to five cells that change under
transpose. The wider validator domain is not a claim of exhaustive sampling.

The four query profiles are `8×8`, `20×24`, `24×26`, and `30×30`, with optional
whole-canvas transpose and seed-dependent order. The `30×30` profile contains
eight substantive tiles: 24 source components, 112 occupied cells, real mergers
and competing sizes throughout the canvas, including all four borders. Colors,
branches, six-cell topology, positions and orientation vary within the
constructive profiles; this is not an unrestricted polyomino sampler.

## Recorded checks and teaching repair

Evidence paths below are relative to the packet's `WORK/` directory.

- `checks/7071285d78ce/native-tests-final.xml`: 111 passing tests: 28 family,
  66 sampler and 17 adapter tests.
- `checks/7071285d78ce/audit-r2/audit.json`: seeds 0 and 17, all three settings,
  three demonstrations and four queries; 168 rival comparisons, 152 refuted by
  demonstrations, and 16 finite-consistent comparisons whose tested queries all
  agree. There are zero query conflicts or execution errors, 347 protected
  Racket executions, and five checked canonical pairs. Source bytes remained
  unchanged during the audit.
- `checks/7071285d78ce/boundaries.json`: 30 protected labels from one maximum-seed
  six-demonstration/four-query request under each setting.
- `checks/7071285d78ce/self-review-repair-proof.json`: 29 protected executions
  confirm two original teaching gaps and their repair. For seed 0 with
  `smallest`, both “transpose only nonsquare bboxes” and “transpose only source
  objects of at most five cells” fit all three original demonstrations but
  conflicted on query indices 0, 1 and 3. Revised demonstration index 1 refutes
  both. The intended program and all four query inputs and labels are unchanged.

The original failing lesson and source snapshot remain under
`checks/7071285d78ce/self-review-nonsquare-v1/`. The earlier audit is retained as
superseded evidence. The current audit covers wrong ordering, transforms,
anchors, connectivity, area definitions, tie handling, color grouping and
conditional shortcuts. Runtime errors never count as refutations. These are
finite checks against declared rivals, not proof of universal identifiability.

Native reviewer qualification passed all six jobs with 78 protected Racket
evaluations (`checks/7071285d78ce/qualification/`). The source-bound causal
witness under `checks/7071285d78ce/causal/` contains two wrong-order cases,
one each for largest and smallest selection. Their counterfactual outputs
change 13 and 10 cells, respectively; construction and independent replay each
used four protected evaluations. Intermediate values and the causal explanation
remain authored metadata, rather than a general proof of algorithmic depth.
The saved public preview exported and verified 24 one-query views under
`checks/7071285d78ce/preview/`. The separate `public-rejections.json` probe
rejects all three mutations: a leaked query answer, an orphan public file, and
a missing public view. The original 24-view bundle remains unchanged. These
projection checks do not perform another Racket replay.

## Portable reproduction

Run from the packet outer directory using its ready interpreter. Payloads run
in `WORK/repo`, so `../checks` refers to `WORK/checks`. Choose fresh output paths.

```sh
WORK/.venv/bin/python review.py run python3 generators/7071285d78ce/workspace/parametric/audit.py --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/7071285d78ce/audit-new
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 7071285d78ce --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/7071285d78ce/qualification-new --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/7071285d78ce/qualification-new/qualification.json --out ../checks/7071285d78ce/preview-new
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/7071285d78ce/preview-new
```

Qualification requires a current native source inventory. Refresh it after
source changes with the documented `arcpuzzles parametric manifest` helper;
replacement requires the exact old manifest hash. Inventory creation does not
qualify or accept the family. Qualification, causal replay and public-preview
verification bind their recorded source and receipt bytes; later source edits
require fresh evidence.

Only a single saved turn under a public preview is model-visible. Private
receipts contain programs, settings, future queries and answers. Reveal queries
one at a time after the preceding answer, without total-count or final-turn
hints. Saved-view verification checks serialization and projection; it does
not itself replay Racket. Reviewer qualification still requires separate owner
acceptance of the exact integrated source. No training admission is claimed.
