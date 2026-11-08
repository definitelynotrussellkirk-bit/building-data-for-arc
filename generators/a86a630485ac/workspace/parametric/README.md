# Native object symmetry and conditional ranking — `a86a630485ac`

One fixed setting applies to every demonstration and query in an episode:

| Parameter | Values | Canonical default |
|---|---|---|
| `axis` | `lr`, `ud` | `lr` |
| `keep_policy` | `all`, `largest_eligible` | `all` |

Objects are nonzero monochrome four-connected components. Classify each
component by reflecting its occupied cells through its own bounding-box center
along the selected axis. Keep every eligible component for `all`. For
`largest_eligible`, keep **all** eligible components tied for maximum occupied
cell count. Preserve their exact cells, locations, holes and colors, and erase
everything else. Empty eligibility produces an all-zero output. The exact
selected canonical text in `canonical.rkt` is returned for `lr/all`.

## Dependency and limits

**A** discovers components and classifies symmetry. The **intermediate** is the
eligible component set with its occupied-cell counts. **B** ranks within that
set and paints all maximum-size eligible components. Computing the global
maximum first, then filtering by symmetry, is a different order: the retained
cores contain a larger asymmetric object that causes that rival to return blank.
The causal witness changes only the set supplying the maximum. This is a
selection dependency, not iterative simulation or a claim about training gains.

The native rule grammar is exact-integer color grids with dimensions 6–30,
background zero, and monochrome four-connectivity. Separate objects may share
a color, touch diagonally with the same color, or touch orthogonally with
different colors. Reference semantics remain total even when no objects are
eligible. Sampler scenes contain multiple eligible and ineligible objects;
empty-scene and empty-eligibility tests check totality separately.

This is a separate extension. The production generator retains version 3.2.0,
its 6–10 by 8–12 dimensions, two-to-four-object distribution, small shapes and
unique color per object. Those production overrides are not expanded here.

## Constructive curriculum

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0 through 2**63−1, independently 2–6 demonstrations and 1–4 queries. The full
six-demo/four-query input bank is constructed before slicing. Inputs are matched
across settings. Input, setting and query-order randomness use separate streams;
the four query profiles are shuffled independently of counts. No rejection
sampling or silent count reduction is used.

The first 11×23 core teaches tied maxima for both axes, a smaller eligible
object, matched-size/matched-box LR-only and UD-only shapes, and a larger
asymmetric distractor. Repeated colors, same-color diagonal contact and
different-color orthogonal contact make component identity visible. Its LR
maximum is seven occupied cells and its UD maximum is five.
The eight-cell asymmetric object has symmetric row and column count projections,
so counting occupied cells per row/column cannot replace reflection of the bitmap.
Its diagonal contact chain reaches a largest LR winner as well as the plus,
making four- versus eight-connectivity observable under every setting.

The second 15×23 core reverses that relationship: LR maximum sixteen and UD
maximum seventeen. Dense smaller shapes beat sparse 7×7 shapes by occupied
count, while the bounding-box-area rival chooses differently. This also teaches
even-sized, doubly symmetric eligibility and unique maxima, alongside the first
core's ties. Both cores are retained for every supported demonstration count.

Further profiles include 6×8 boundary scenes, 14×20, 18×24, 23×29 and 26×27
rectangles, rings and larger asymmetric/symmetric shapes. The 30×30 demo/query
scenes contain nine objects and over 300 occupied input cells. Four dense
corner objects of size 8×8 or 7×7 are tied eligible winners; an 80-cell
asymmetric object must first be excluded. Even the maximum-only outputs retain
at least 196 cells across all four quadrants. Content reaches all four borders.

Palette permutations, object-slot permutations, within-slot translations and
independent left-right/up-down reflections vary the scenes. Shapes come from
the documented constructive recipes; unrestricted polyomino sampling and
coverage of every legal dimension are not claimed. Ninety-degree rotation is
not advertised as label-invariant because it exchanges the symmetry axes.

## Evidence and use

Focused tests are `tests/test_native_family.py` and `tests/test_native_audit.py`.
The task-local `audit_native.py` tests demonstrations against finite executable
rivals with an independent Python oracle and protected Racket labels. Current
sampler, teaching, qualification/execution and causal witness/replay evidence
is under `checks/a86a630485ac/`; native source inventory is
`evidence/manifest.json`. Qualification uses six demonstrations to cover the
entire bank. The separate teaching check uses the minimum two.

From the outer packet folder, with its selected Python environment:

```bash
python3 review.py run python3 -m pytest generators/a86a630485ac/tests/test_native_family.py generators/a86a630485ac/tests/test_native_audit.py
python3 review.py run python3 -m arcpuzzles parametric qualify a86a630485ac --demos 6 --queries 4 --out ../checks/a86a630485ac/qualification-new --summary
python3 review.py preview-public export --qualification ../checks/a86a630485ac/qualification-new/qualification.json --out ../checks/a86a630485ac/preview-new
python3 review.py preview-public verify --bundle ../checks/a86a630485ac/preview-new
```

Choose fresh output paths. Give the model only one chosen
`public/<sha256>.json` file: it contains demonstrations and one current query
input, with no query answer, setting, program, seed, future query or count hint.
Keep directory inventories and `private/` with the existing controller. This
projection adds no turn controller and does not replay Racket. Native owner
qualification and acceptance of both exact integrated builds remain separate;
no training data or training activation is admitted by this return.
