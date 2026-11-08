# Nearest object under Manhattan or Chebyshev distance

The private episode parameter is `metric: manhattan | chebyshev`. Remove the
single marker 9, discover same-color cardinal components, and select the object
whose nearest occupied cell minimizes the chosen distance. Resolve ties by bbox
top, then left; a complete key tie preserves row-major component discovery order.
Reconstruct only the winning component in a fresh zero-filled tight bbox.

`manhattan.rkt` is the exact canonical program. `chebyshev.rkt` changes only its
two `pos-manhattan` calls to the existing `pos-chebyshev` primitive. Production
generator, authority and approval remain unchanged. The separate family extends
the input grammar to 5..30 rows/columns and 2..8 monochrome cardinal components
of arbitrary positive size, with one marker and exact integer colors 0..9.
Different-colored neighbors may share an edge; disconnected same-color objects
remain separate. This is the declared family grammar, not every input the
unvalidated canonical program could process.

## Input-dependent computation

The marker and all component cells determine the per-object distances and the
winning object. That derived object supplies the output dimensions, normalized
cell mask and color. The crop cannot be chosen before selecting the winner.
The native causal witness substitutes Manhattan distances in the qualified
Chebyshev setting: the first example then selects A instead of B, changing the
output from a 14×8 bent object to a 9×3 bent object. It is a concrete dependency
in selection and reconstruction; no iterative-state claim is needed.

## Teaching and query contract

`adapter.generate(seed, settings, demos, queries)` supports exact integer seeds
`0..2**63-1`, independent `demos=2..6` and `queries=1..4`. Ordinarily use three
demonstrations and four controller-side queries. The first two demonstrations
are constructive, palette-varied and translated; later demonstrations vary size,
shape and placement. Inputs match across metric settings. Seed/split/index RNG
streams and distinct input dimensions preserve the first query when counts vary.

| First teaching scene | Selected component | Distance | Output shape |
|---|---|---:|---|
| Manhattan setting | A | 7 | 9×3 |
| Chebyshev setting | B | 5 | 14×8 |
| Tested Euclidean rival | E | Squared distance 45 | 2×2 |

Both actual winners have same-color diagonal satellites and differently colored
edge-touching intruders. These expose eight-neighbor grouping, whole-color
grouping, color-blind connectivity and raw input cropping. The second scene has
B/C/D tied at distance one: B wins bbox ordering despite C being discovered
earlier and D having a smaller bbox column. Another object's bbox contains the
marker despite its nearest occupied cell being farther away. The selected crop
must erase the marker, other objects and a disconnected same-color center cell,
while preserving a real hole.

Four query profiles are 12×15/4 components, 20×24/6, 30×30/8 and 25×29/7.
Boundary frames plus internal solid, frame, comb, elbow and notched objects
provide real content across the canvas. The 30×30 checks require at least 250
candidate cells, including at least 150 interior cells. Query zero includes
marker contact; later queries prefer a separated marker. The ordinary generated
profiles are larger than the 5×5 grammar boundary, which has a literal Racket check.

## Reusable bounded audit

From the outer issued review directory, with its configured Python and Racket:

```bash
python3 review.py run python3 \
  generators/25e18d9bd322/workspace/parametric/audit.py \
  --out ../checks/25e18d9bd322/new-audit
```

Use a fresh output path. The retained audit generated 24/24 episodes: both
settings, seeds 0/17/29/maximum, demo counts 2/3/6, and four queries. All 22
declared Python rivals were rejected by demonstrations. `rivals.py` implements
the other metric, Euclidean distance, bbox origin/region, centroid, mean distance,
farthest, reading-order first/last, size/color extremes, three tie shortcuts,
eight-neighbor/color grouping, color-blind connectivity, raw crop, solid bbox
and hole filling. This is finite coverage, not universal identifiability.

Protected Racket performed 48 evaluations for four jobs at demo-count endpoints
on seed 29, plus four literal evaluations for 5×5 marker contact and complete-key
ties in both settings. Native qualification separately exercises seeds 0 and 17
at three demos and four queries. The isolated task suite passed 42 tests,
including exact canonical labels and a regression for nested metadata scrubbing.

## Public examples and source binding

`evidence/current/public/` holds two hash-named four-query controller challenges.
Only one file from `public_turns/` should reach an actor on each user turn.
`adapter.public_turn` whitelists training input/output and exactly one query
input, dropping top-level and per-pair private metadata. It gives no future
query, count hint, setting, seed, program or query answer. First-turn bytes equal
single-query use, and public IDs hash only the existing helper's public bytes.

`private.json` maps controller/turn IDs to settings, programs, query labels and
teaching checks. Keep it and `execution.json` private. The worker's generic
reference string grants no acceptance: the example records explicitly mark
owner acceptance pending and training admission false. The native
`evidence/manifest.json` inventories exact source, tests and evidence. This is
a reviewer proposal; the owner must qualify and accept exact integrated bytes
before using the accepted-family export path.
