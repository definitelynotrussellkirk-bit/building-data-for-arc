# Area-matched object scaling

**Status: reviewer-ready, native-qualified; owner acceptance pending.**
The production generator and its canonical authority were not edited. The
separate family has `scale=1|2|3`, default `2`, and independent 2–6 demonstration /
1–4 query counts. Use three demonstrations and four queries for ordinary work.

## Reproduce and use

From the packet's outer folder, with its passing Python interpreter:

```sh
python3 review.py run python3 -m pytest -q \
  generators/a0444de97675/tests/test_parametric_a0444de97675.py
python3 review.py run python3 \
  generators/a0444de97675/workspace/parametric/verify.py \
  --out generators/a0444de97675/workspace/parametric/evidence/NEW-DIRECTORY
python3 review.py run python3 -m arcpuzzles parametric qualify a0444de97675 \
  --demos 3 --queries 4 --out ../checks/a0444de97675/NEW-QUALIFICATION --summary
```

`adapter.generate(seed, {"scale": 2}, 3, 4)` returns all four controller-side
queries with private labels. Python outputs are claims until independently
checked by Racket. The existing native qualification/export path checks those
labels; the adapter does not grant approval. After owner integration, fresh
qualification and exact-source acceptance, the normal public API is:

```sh
python3 -m arcpuzzles parametric export a0444de97675 --count 4 --seed 17 \
  --demos 3 --queries 4 --out var/datasets/area-scale-s17
```

Before source edits, inspect the existing source-bound inventory and evidence.
After edits, write evidence to a fresh directory and rebuild the manifest with
the native helper, using its guarded replacement option. Never copy an old
qualification to claim new bytes passed.

## Teaching, sizes, and causal dependency

Inputs are identical across the three scale settings. Random streams also keep
the first demonstrations/query stable when counts change. The first demo has a
foreign cell within the target crop; the second has a clean target. Their target
area ranks differ. The two demos must reject all declared wrong rules before
queries are generated; a bounded retry changes only the second demo. The tested
60-episode sample needed at most one extra demonstration draw.

The sampler covers exact heights 8–30 and widths 9–30. Default query sizes are
13×15, 21×24, 24×27, and 30×30. Large scenes add cells and objects across the scene;
the retained 30×30 stress case has 11 monochrome objects, 202 occupied body cells,
and occupied spans of 29 rows and 30 columns. Each selected crop is at most
10×10, keeping all scale-3 outputs within ARC's 30×30 bound. Slot construction is
a restriction of this proposed sampler, not a restriction on the canonical rule.

Step A counts blue header cells to produce K. Step B uses K to select the unique
monochrome object of that area, then reads its crop from the original grid. The
retained causal witness uses K=10 versus an incorrect all-nonzero count of 11;
protected Racket selects different objects and returns different outputs. This
is an input-derived selection dependency, not a claim of iterative simulation.

## Evidence and limits

- `evidence/verified/summary.json`: 60/60 bounded Python episode requests, 26
  declared rivals including the selected scale, zero ambiguities; matched inputs,
  strict counts and stable first-turn projection.
- `evidence/verified/examples.private.json`: six protected-Racket examples,
  covering all scales at two and six demos, each with four queries; 48 labels.
- `evidence/verified/teaching.private.json` and `stress.private.json`: executed
  wrong-header/connectivity predictions and exact size-boundary labels. Together
  with the examples and five canonical pairs, the builder made 125 Racket calls.
- `WORK/checks/a0444de97675/qualification/` in the return: six native jobs at
  seeds 0/17 with three demos/four queries; 42 labels and 78 Racket evaluations.
- `WORK/checks/a0444de97675/causal/`: native source-bound witness and replay.
- `WORK/checks/a0444de97675/portable-tests/`: all 31 canonical/parametric tests
  passed again in the isolated staged task runtime.
- `../../counterexamples/parametric-teaching-gap/`: the original failed lesson,
  two executable alternatives, and 18 protected-Racket replay evaluations.
  These preserve the before-fix defect; the regression checks the repaired two
  demos for original seeds 0 and 17.

The first implementation omitted mixed-group and fixed-rank rivals. Both fit
the original two-demo lesson and failed later queries. The clean second demo
and rank-refuting selection repair those observed holes without adding demos.
Finite rivals and seeds do not prove universal uniqueness or training benefit.
Production acceptance, training admission and mixture allocation remain separate.

## Public projection

Give the existing consumer `{"train": episode["train"], "test": [query]}`
through `reviewer_support.public_challenge_bytes`; derive its filename with
`public_challenge_id`. The saved `evidence/verified/public/` files contain only
first-turn demonstrations and one query input. Each filename hashes exactly
those bytes. The six files passed the packet's public export checker.
Settings, seeds, programs, answers, total-query counts and future inputs stay
private. The one-query draw and first turn of the four-query draw are identical.
No turn controller or training loop is added.

## Design and implementation plan

Goal: preserve header counting, monochrome component selection and original-grid
cropping while teaching an episode-fixed `scale` in `{1,2,3}`. The default `2`
uses the exact existing canonical Racket program. This is a separate parametric
extension; the approved production generator and authority remain unchanged.

The implementation uses Python 3.12 and the packet's protected Racket runtime.
A task-local sampler supplies matched inputs across settings, constructive
teaching examples, 2–6 independent demonstrations and four novel queries.
One-query requests are supported for checking identical first-turn projection.
The useful causal dependency already exists: count the header to obtain K,
then choose the unique area-K object and crop its input-dependent bounding box.

Alternatives considered: varying only the grid sampler would not parameterize
the rule; replacing object selection would change the core puzzle. Varying the
scale retains its reasoning and makes the hidden setting directly teachable.
These are implementation choices made for this review, not owner acceptance.

- [x] Add focused tests for exact canonical source, counts, matched inputs,
      typed bounds, source-crop semantics and nontrivial 30×30 scenes.
- [x] Implement `adapter.py`, `prototype.py`, `canonical.rkt` and the native
      `promotion.json` contract. Keep imports and resources in this task home.
- [x] Execute bounded label/teaching checks through protected Racket; check the
      public projection with existing helpers. Record finite-rival limits.
- [x] Build the native inventory, qualify exact sources, and retain a protected
      wrong-intermediate witness before preparing the return package.

Review focus: two-demo teaching, cells versus color-agnostic components,
original-grid crop versus isolated-object crop, scale-3 output bounds, and public
query isolation. Tests and the small evidence builder cover these surfaces.

The extraction is already isolated and has no Git metadata. The source patch is
the packet-native deliverable; no separate Git branch or broad battery is needed.
