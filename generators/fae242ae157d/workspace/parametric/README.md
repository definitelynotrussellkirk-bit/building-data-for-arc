# Area rank and distance from the largest object

This is a separate native parametric family for `fae242ae157d`. The selected
production generator and canonical reference are unchanged. The default program
is copied byte-for-byte from the public catalog. Reviewer qualification is not
owner acceptance or training admission.

## One rule parameter

| `ranking_policy` | Transformation |
| --- | --- |
| `area` | Paint the smallest, middle and largest objects 2, 3 and 4. Exact canonical program. |
| `nearest_largest` | Find the largest object by occupied cell count and paint it 4. Paint the nearer remaining object 2 and the farther one 3. |
| `farthest_largest` | Find the same largest object and paint it 4. Paint the farther remaining object 2 and the nearer one 3. |

Distance means the minimum Manhattan distance between any occupied cell of an
object and any occupied cell of the anchor. The input-dependent anchor is needed
before either distance can be evaluated: a bounding-box, color, or fixed-position
anchor can change the final labels. The alternative settings retain the source
task's object discovery, actual occupied counts, rank inference and recoloring.

The common admitted grammar is a rectangular ARC grid no larger than 30×30,
background 0, exactly three separated monochrome four-connected objects, at
least three cells per object, distinct occupied areas, and distinct distances
from the two smaller objects to the largest. Same-color diagonal contact is
allowed. There is no distance-tie policy. The strict Python entry point rejects
booleans, floats and malformed grids. This grammar deliberately widens the
production sampler's six fixed dimensions and 3–12-cell objects; it does not
change that sampler's acceptance rules.

## Three teaching examples, four novel queries

`generate(seed, settings, demos, queries)` supports 3–6 demonstrations and 1–4
queries independently. Seeds are literal integers in 0..2**63−1. Settings are
fixed for the episode; every policy receives identical input grids for a given
seed. Separate SHA-256-derived input streams and complete six-demo/four-query
banks make all count requests prefix-compatible. Duplicate inputs trigger at
most 64 slot-local attempts, then fail visibly. Results are fresh arrays and do
not alter the process's global random state.

The first three scenes deliberately distinguish actual cell counts from bounding
boxes/perimeters, four-connectivity from eight-connectivity, and minimum
Manhattan distance from centroids, bounding boxes, Euclidean distance and
Chebyshev distance. A small line's placement in the second demonstration is
essential: its Manhattan distance is 6 versus 7, while Euclidean squared
distances are 36 versus 29 and Chebyshev distances are 6 versus 5. No fourth
demonstration is needed for that distinction. The first scene's orientation
preserves a counterexample to using only bounding-box top-left corners.

Queries cover 9×11 (or its rotation), 18×24 (or its rotation), 24×24 and 30×30.
The larger scenes use connected boundary-spanning objects with variable internal
voids. The 30×30 query contains 370–450 occupied cells and touches all four canvas
edges; its answer is also 30×30. Queries exercise ordinary area triples 4/5/6,
larger occupied counts, monochrome and distinct-color scenes, rotations and
reflections. Three structured teaching profiles and a bounded rival set are not
proof against arbitrary unseen rules or a measurement of training benefit.

`public_turn(episode, index)` returns the same demonstrations and exactly one
query input. It emits no query output, setting, seed, program, future input,
total-query count or final-turn hint. The first view is identical for one-query
and four-query requests. The consumer remains responsible for sequential reveal.

## Reusable execution and audit tools

`native_family.py` owns the rules and sampler; `adapter.py` loads it by exact
adjacent path. Deterministic Python labels are claims, independently executed by
the existing protected Racket worker. No Racket audit runs inside `generate`.

`audit.py` executes intended labels and declared rivals, screens only the first
three demonstrations, and checks queries only for surviving rivals. Every
screened example must execute, even after an earlier refutation; a runtime error
cannot count as teaching evidence. It also replays the four official pairs,
checks matched inputs/count prefixes, and exports strict one-query public files.
Public files and their physical publication order use hashes of exact visible
bytes. The serialized verifier checks hashes, types, distinctness, coverage and
public/private correspondence. It does not authenticate a fully rewritten bundle
or perform a fresh Racket execution.

`distance_lesson_probe.py` retains a small authored precursor lesson in which
Euclidean and Chebyshev alternatives fit all three demonstrations and disagree
on a query. It executes the alternatives and checks the repaired demonstrations.
These are authored research counterexamples, not extra official answers or an
ambiguity in the production generator.

From the packet's outer directory, with its prepared interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -B \
  generators/fae242ae157d/workspace/parametric/audit.py \
  --out ../checks/fae242ae157d/new-audit --seed 0 --seed 17
WORK/.venv/bin/python review.py run python3 -B \
  generators/fae242ae157d/workspace/parametric/distance_lesson_probe.py \
  --out ../checks/fae242ae157d/new-distance-lesson.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  fae242ae157d --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/fae242ae157d/new-qualification --summary
```

Use fresh output paths. The native inventory must be current before qualification;
the owner must integrate, qualify and accept exact live bytes before this family
becomes available through accepted-parametric export.
