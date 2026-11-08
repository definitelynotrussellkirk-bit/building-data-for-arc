# Native projection reach: one step or to the boundary

This completes the existing task-local projection-reach prototype for
`48bda9528e71`. The two settings and the original projection implementation are
retained. The native adapter adds an exact canonical default, a larger validated
input domain, constructive teaching examples and independent count-stable banks.
Production version `2.1.0`, its source, selected rule and approval are unchanged.
Owner qualification and fresh acceptance remain pending after integration.

## Rule and geometric dependency

The input contains one occupied shape on background **8**, using two or three
foreground colors. Select the unique least-frequent foreground color. For each
active row, derive the actual left/right occupied endpoints; for each active
column, derive its top/bottom endpoints. Erase the source and use the selected
color for the episode-fixed projection:

| `projection_reach` | Output |
|---|---|
| `one_step` | One in-bounds cell immediately beyond each endpoint |
| `to_boundary` | Every cell from just beyond each endpoint to the canvas edge |

The intermediate is the collection of per-row and per-column extent tables,
plus the rare color. Projection positions consume those tables. On a concave
shape, substituting its global bounding-box endpoints changes spatial output
while retaining the same color and reach. This is the causal counterfactual;
it does not rely on merely changing the paint color or reordering erasure.

The native default returns the exact selected bytes in `canonical.rkt`.
The alternative reuses `prototype.program_for("to_boundary")`. The existing
projection loops were factored into `prototype.project_extents`, which both
legacy `apply_python` and the native family call after their respective input
validators. No second Python projection implementation is maintained.

## Grammar, curriculum and API

Native inputs are square exact-integer ARC grids from 5x5 through 30x30. Color 0
is legal foreground. The occupied shape is four-connected and orthogonally
convex: every active row and column is a contiguous interval. It spans at least
three rows and columns, has 7..floor((n*n-1)/2) cells, uses two or three colors,
and exposes at least four in-bounds extent markers. Its rare color is unique,
and every cell of that color has four occupied cardinal neighbors. The area
bound keeps background 8 strictly modal. Concave notches remain lawful;
Euclidean convexification changes the intended answer.

`adapter.generate(seed, settings=None, demos=3, queries=4)` supports exact integer
seeds in `0..2**63-1`, independently selected demo counts `3..6`, and query counts
`1..4`. An omitted setting selects from the two modes by seed parity once for
the episode. All settings share input banks. Each role has its own SHA-256-derived
local RNG stream. Six demos and four queries are constructed before slicing,
so changing a demo count does not move the query inputs. Results are fresh and
do not alter global RNG state; malformed controls fail explicitly.

The mandatory three demonstrations include a broad concave cross, an edge-clipped
notched shape, and stairs. They vary the rare count and two/three-color structure.
The first spreads rare cells across interior arm locations while a more frequent
compact color-zero patch occupies the geometric center and has a smaller color
bounding box than its nonzero rare color. The second uses a thin-arm notch with
rare color nine at its sole interior elbow and common foreground zero. The third
uses one rare zero cell, color nine on every other interior cell, and a third
color on the occupied boundary. Nine is then the most frequent foreground color,
but its enclosed geometry cannot supply the whole shape's extents. These roles
distinguish frequency-based selection from fixed color, numeric color order,
center location, color bounding-box and dominant-color geometry shortcuts. The
thin-arm case also separates total color frequency from interior-cell counts
and monochrome component-count ties. Optional demos add rectangle, diamond and
shifted-stair controls. There is no generation retry loop.

Four queries are exactly 5x5, 16x16, 24x24 and 30x30, with respectively 12, 96,
221, and 275 or 371 occupied cells. The largest cross spans and touches all four
canvas edges. Shape orientation, geometry, palettes, frequency counts, placement
and margin/clipping conditions vary across roles and seeds. This is a structured
finite constructor family, not every lawful orthogonally convex polyomino.

## Runnable native checks

From the extracted packet outer directory, payload paths resolve in `WORK/repo`.
Always choose new evidence destinations:

```sh
WORK/.venv/bin/python review.py run --receipt checks/48bda9528e71/recheck.json \
  python3 -m pytest generators/48bda9528e71/tests/test_native_family.py \
  generators/48bda9528e71/tests/test_native_sampler.py \
  generators/48bda9528e71/tests/test_native_adapter.py \
  generators/48bda9528e71/tests/test_parametric_projection_reach.py \
  generators/48bda9528e71/tests/test_parametric_projection_reach_verifier.py -q

WORK/.venv/bin/python review.py run --receipt checks/48bda9528e71/rival-recheck.json \
  python3 generators/48bda9528e71/workspace/parametric/audit.py \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/48bda9528e71/rival-recheck

WORK/.venv/bin/python review.py run --receipt checks/48bda9528e71/requalify.json \
  python3 -m arcpuzzles parametric qualify 48bda9528e71 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/48bda9528e71/requalification --summary
```

The adjacent generic auditor runs protected Racket, caches exact program/input
pairs, hashes its source scope, and distinguishes demo refutations, consequential
query conflicts, finite consistency and execution errors. Its programs and
labeled episodes are private evidence. The finite menu covers global bbox,
convexification, color-subset geometry, one-axis projection, wrong reach/endpoints,
shape retention and plausible color selectors. Exact lattice convexification is
also checked on a literal notched example. An exterior cardinal shell equals
one-step projection on this admitted grammar; such agreement is not a defect.

The task-scoped boundary helper accepts `--out NEW.json`, refuses overwriting
prior evidence and measures occupancy/span/edge contacts against the family's
declared background, including foreground zero. The public probe uses the
native saved projection and rejects leaked query labels, orphan public files
and missing views in temporary copies. The verifier checks serialization and
source binding without claiming a fresh Racket replay.

## Historical compatibility and evidence limits

Independent review confirmed eight cases of three color-selection shortcuts
on the initial three-demo prefix: fewest interior cells, most monochrome
components with numeric ties, and highest fully enclosed color. Exact programs,
grids, labels and frozen baseline sources remain in `checks/48bda9528e71/`.
The repaired second demo uses a one-interior-cell notch with rare nine and
common zero. The first demo remains unchanged, retaining an enclosed common-zero
color below its nonzero rare color. An intermediate repair of the third demo
refuted the observed color selectors but exposed four protected failures of
dominant-color-only geometry: its boundary color still supplied every true
extent. The final third demo makes enclosed nine dominant, with counts 35 versus
34 or 54 versus 41 and a single rare zero. Both directions of numeric enclosure
and the dominant-color geometry shortcut are therefore refuted. This last repair
keeps the first two demos byte-identical, retains the third occupied mask and
orientation, and selects its rare cell from its former five-cell rare set.

These changes retain three demos. All twelve query inputs at seeds 0, 17 and
`2**63-1` remain byte-identical. All three exact observed color rivals, the
opposite enclosure guard and dominant-color geometry are included in the final
reusable audit menu; the eight original observed cases are replayed. Earlier
failed and intermediate reports remain retained and are not current-source
verification.

The legacy `prototype.generate_episode` and CLI retain their old contracts and
metadata, and `verify.py` remains available for their historical workflow. Their
public examples expose all query inputs and are not the new sequential view.
Use the native qualification and packet `preview-public` exporter for this build;
each new model-visible file contains demonstrations and exactly one current query
input, with no future input, count hint, hidden settings, code or query answer.

Historical programs, episodes, manifests and reported results remain retained.
The current native inventory is rebuilt with an exact-hash replacement guard and
binds the new source and focused evidence. Old reports do not prove current
checks. Finite validation does not establish universal identifiability or measured
learning benefit. Reviewer readiness grants neither owner acceptance nor training
admission. Production batteries were not rerun for this separate prototype work.
