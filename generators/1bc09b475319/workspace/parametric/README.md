# Native bar caps and bridges — 1bc09b475319

One episode-fixed parameter `cap_mode` has two values:

| Value | Rule |
|---|---|
| `caps` (canonical default) | Paint 8 into a zero cell immediately beyond two consecutive horizontal 6s. Preserve every other cell. |
| `bridge_caps` | Make those caps, then join vertically aligned consecutive **new** caps only when their entire intervening column segment is zero. Paint the clear segment 8. |

The default returns the exact selected canonical text in `canonical.rkt`.
The separate native grammar accepts rectangular exact-integer color grids with
height/width 7–30. The rule is total on that grammar, including blank inputs,
preexisting cyan, arbitrary other colors, occupied cap sites and no-bridge scenes.
Production version 3.1.0 and its 7–18 by 7–20, bar-length-2–5 sampler are separate.

## Dependency

**A** identifies newly eligible cap positions and paints the capped grid.
The **intermediate** is that input-dependent position mask together with the
capped grid. **B** sorts new cap rows within each column and fills every clear
interval between consecutive anchors. Existing 8s never become anchors; any
nonzero interior cell, including an existing 8, blocks the entire interval.
All interval decisions use the frozen capped grid. Filled bridge cells never
create a new round of anchors. A bridge can join a left cap to a right cap.

The counterfactual changes the anchor binding from newly derived caps to input
8s while retaining the correctly capped grid. This is a spatial mask dependency,
not iterative simulation or a claim about model training gains.

## Constructive curriculum and boundaries

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0 through 2**63−1, independently 2–6 demos and 1–4 queries. Omitted settings are
chosen deterministically from a separate RNG. Geometry and query-order streams
are separate from settings and counts. The full six-demo/four-query bank is
constructed before count slicing; inputs match across settings. There is no
rejection loop, duplicate filler, or silent count reduction.

The first 13×19 core combines long/short/edge bars, vertically adjacent singleton
distractors, opposite-side vertical cap alignments and an intentionally unfilled
horizontal between-cap gap. The second 15×23 core has three anchors per column,
independently blocked upper gaps and clear lower gaps, old cyan anchor decoys,
occupied cap targets and a six-cell edge bar. An old-cyan-only blocker is
explicitly taught. Both cores remain present at the minimum two demos.

Further demo profiles are 7×7, 18×22, 24×27 and 30×30. Queries are 7×9, 16×21,
25×29 and 30×30 in an independently shuffled order. Larger fields contain many
mixed-length horizontal runs and cap alignments across the canvas, blockers,
singletons and existing cyan. The two 30×30 profiles differ structurally in
their full-width edge bars and contain over 200 occupied input cells. Both
touch every boundary. Their structure exercises many separate cap and bridge
decisions, beyond empty padding.

Variation includes row translations of the cores, horizontal/vertical
reflections, blocker-color permutations and field length phases. The sampler
is a finite constructive profile bank; unrestricted layouts, every legal
dimension and universal rule uniqueness are not claimed. Ninety-degree
rotation is not label-invariant for this horizontal-cap/vertical-bridge family.

## Evidence and use

Focused tests are `tests/test_native_family.py` and `tests/test_native_audit.py`.
The independent `audit_native.py` checks finite executable wrong rules against
the two visible core demos, executes surviving queries, and checks intended
labels across the entire bank. Source inventory is `evidence/manifest.json`;
current sampler, teaching, qualification/execution and causal evidence live in
`checks/1bc09b475319/`. Python claim labels do not replace Racket qualification.

From the outer packet directory, use the selected Python environment:

```bash
python3 review.py run python3 -m pytest generators/1bc09b475319/tests/test_native_family.py generators/1bc09b475319/tests/test_native_audit.py
python3 review.py run python3 -m arcpuzzles parametric qualify 1bc09b475319 --demos 6 --queries 4 --out ../checks/1bc09b475319/qualification-new --summary
python3 review.py preview-public export --qualification ../checks/1bc09b475319/qualification-new/qualification.json --out ../checks/1bc09b475319/preview-new
python3 review.py preview-public verify --bundle ../checks/1bc09b475319/preview-new
```

Use fresh output paths. Give the model one selected `public/<sha256>.json`
at a time. Keep answers, settings, programs, future queries and file listings
with the controller. The export uses the existing native projection and adds
no turn controller. Owner qualification and fresh acceptance of both exact
integrated sources remain separate. No training admission or activation.
