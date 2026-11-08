# Native seeded frames and filled-component selection — 486375757aca

The episode fixes `post=none|largest_to_8`; `none` returns the exact canonical
program. First find all monochromatic cardinal blue (1) components in the
**original input**, in row-major order of their first occupied cell. For each
component, scan its bounding-box interior in row-major order and choose the last
original value other than 0 or 1. Fill its entire strict interior with that
color, including earlier seeds and internal blue cells. Object extraction and
seed reads stay frozen; writes accumulate in component order. Touching frames
merge, and nested or overlapping component boxes remain supported.

`largest_to_8` then finds monochromatic cardinal components in the **completely
filled grid**, excludes colors 0 and 1, and recolors every whole component tied
for largest occupied-cell count to 8. Freestanding colored components participate.
Disconnected components of the same color remain distinct. Measure occupied
area, not bbox area; determine all winners before painting. Output dimensions
always equal input dimensions.

## Causal dependency

**A** performs the canonical fill, creating and changing colored components.
The **intermediate** is the resulting grid and its component geometry. **B**
measures those components, selects the largest ties and paints their cells.
The counterfactual keeps the correctly filled grid but supplies B with component
masks and sizes from the original input. It changes which cells are recolored.
This is an input-dependent state transformation followed by selection; it is not
a claim about iterative simulation or measured training gains.

## Native grammar

Inputs are rectangular lists with axes 3–30 and exact integer colors 0–9. There
must be at least one blue component, and every blue component's bbox must contain
at least one original non-{0,1} seed in its strict interior. These conditions
also guarantee an eligible post-fill color component. Seeds outside all blue
boxes and open blue shapes with seeded boxes are allowed as explicit extensions.
Complete rectangles are used by the constructive sampler, while literal tests
also cover open blue geometry. The grammar does not require disjoint boxes,
unique seed colors, a single seed per frame, or an intact inner frame after filling.

This separate family leaves production v3.0.0 and its inherited seed/sample-index
coercion finding unchanged. Strict native controls do not resolve that production
API finding or its audit disposition.

## Constructive episodes

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0 through 2**63−1, 2–6 demonstrations and 1–4 queries independently. Settings use
a separate random stream; inputs are matched across the two settings. Construct
the full six-demo/four-query bank before slicing, with independent query ordering.
All loops have finite geometric bounds, with no rejection or shortened requests.

The first two demonstrations supply complementary witnesses:

- A 17×26 core has a merged touching pair, a diagonally touching separate frame,
  repeated seed colors, different first/last/column-major/majority choices, and
  opposite first/last color orders in two nonwinning components. Its largest
  eligible filled component has 48 cells; a thin blue frame has 54 blue cells,
  so blue must be excluded. The opposite seed orders defeat min/max-color rules
  under every permitted palette permutation.
- A 21×26 core has nested boxes and three largest colored components tied at
  72 cells. One is a ring with bbox area 81; one is a filled frame; one is
  freestanding. Two separate same-color components have areas 9 and 70, so
  aggregating by color would select the wrong hue. Original seed reads and
  frozen component order remain visible after the post-operation.

The cores use safe whole-scene translations and palette permutations fixing
0, 1 and 8. Their orientation is fixed because a blind D4 transform can change
row-major seed selection and erase the nested tie witness. The varied mosaics
use D4 transformations and are labeled after transformation.

Additional demo dimensions are 3×3, 13×17, 24×27 and 30×30. Queries are 5×9,
18×23, 27×29 and 30×30, with transposes allowed for mosaics. Variable interval
sizes, seed locations/counts/colors, blue bridges and L-shaped merged groups
produce overlapping bbox writes. The 30×30 demo uses nine frames; the query
uses sixteen. Their blue-cell counts differ (304 versus 376), so those two
roles cannot coincide. Other roles have different dimension pairs. Every bank
therefore contains ten distinct inputs.

Both 30×30 inputs contain hundreds of occupied cells across all quadrants and
touch all four canvas borders. Their labels fill hundreds of cells and process
multiple merged and overlapping components. These are substantive large cases,
not padded small frames. The finite core/mosaic bank does not sample every legal
dimension, blue shape or frame arrangement.

## Verification and use

`tests/test_native_family.py` checks exact default preservation, last-seed choice,
touching/internal-blue behavior, nested order and original reads, component ties,
freestanding eligibility, repeated colors, strict controls, count prefixes,
novel matched inputs and large content. `audit_native.py` has an independently
written parser/oracle and exact executable Racket rivals. It uses only the first
two demonstrations for teaching decisions and checks the complete six-demo/four-
query label bank at fixed seeds. Execution errors never count as refutations.

From the outer packet folder, with its selected Python environment:

```bash
python3 review.py run python3 -m pytest generators/486375757aca/tests/test_native_family.py generators/486375757aca/tests/test_native_audit.py
python3 review.py run python3 -m arcpuzzles parametric qualify 486375757aca --demos 6 --queries 4 --out ../checks/486375757aca/qualification-new --summary
python3 review.py preview-public export --qualification ../checks/486375757aca/qualification-new/qualification.json --out ../checks/486375757aca/preview-new
python3 review.py preview-public verify --bundle ../checks/486375757aca/preview-new
```

Choose new output paths. The source/evidence inventory is `evidence/manifest.json`;
current checks are under `checks/486375757aca/`. Python outputs are claims that
native qualification independently re-executes through protected Racket. Finite
named-rival success does not establish universal identification.

Reveal only one selected `public/<sha256>.json` at a time. Keep settings, programs,
answers, future query inputs and directory listings with the controller. The
existing exporter adds no new turn controller. Owner native qualification and
fresh acceptance of both exact integrated sources remain separate; no training
admission or activation follows.
