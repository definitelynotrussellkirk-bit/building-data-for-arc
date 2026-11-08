# Missing box with one boundary peel

This separate native adapter preserves the reviewed production generator and
the exact canonical Racket program. Its private, episode-fixed parameter is
`peel_depth: 0 | 1`, default `0`.

- **0:** Draw the minimal bounding rectangle of every source marker.
- **1:** Find that rectangle, remove every marker on its perimeter, then
  recompute and draw the minimal rectangle of the surviving markers.

Both outputs use a fresh, same-size zero grid and the source marker color.
This is not a geometric inset: the four inner gaps vary independently, and
noncorner outer markers must be removed jointly by row OR column membership.
The selected outer extrema determine the intermediate set needed for the
second bounding-box inference.

## Domain and counts

The prototype's shared domain is a rectangular grid of **6–30 rows by 7–30
columns**, one marker color in **2–9**, **4–160 markers**, an outer box at least
6×6, and at least two strict-interior markers whose box spans at least 4×4.
Empty/singleton survivors, multiple foreground colors and repeated peeling are
outside this family. There is no implicit fallback to the outer box.

This is an opt-in extension of size and marker density. The production sampler
still has its original 6–12 by 7–14, 2–8-marker domain. The default program is
byte-identical to its authority, including on the original five source pairs.
The prototype does not replace production two-marker teaching witnesses.

`generate(seed, settings, demos=3, queries=4)` accepts exact integer seeds in
`0..2**63-1`, **2–6 demonstrations** and **1–4 queries**, independently. The
default is three demonstrations. The first two are constructive teaching
examples: distributed noncorner extrema with an interior marker to clear,
then exactly two survivors with unequal gaps. They eliminate the declared
query-changing rivals without rejection sampling. Extra demos add sizes and
layouts. Changing settings preserves all input grids for a given seed/request.

Four query profiles are 6×7, 12×16, 22×26 and 30×30. The last two include
48–80 inner markers plus 12–24 outer markers; the 30×30 outer rectangle touches
all four canvas edges and its inner rectangle spans at least 24×24. These are
substantive large scenes, not small shapes padded to the requested dimensions.
All sample slots have distinct dimensions or marker counts, so no retry loop
is needed to make inputs unique within an episode.

## Reproduce the checks

From the outer extracted packet, use its verified Python interpreter. Payload
paths resolve from `WORK/repo`. Choose unused output directories:

```bash
python3 review.py run python3 -m pytest \
  generators/17ea562973ac/tests/test_parametric.py -q
python3 review.py run python3 \
  generators/17ea562973ac/workspace/parametric/verify.py check \
  --out ../checks/17ea562973ac/focused-new
```

The reusable verifier executes both rules through the protected Racket bridge,
checks both settings on every unique input, compares every saved label, checks
five original canonical pairs, fits settings on demonstrations only, audits
finite shortcut rivals, tests public/private separation, and saves complete
private four-query examples plus hash-named one-query public views.

`teaching_check` considers five rivals for depth 0 and fourteen for depth 1.
The latter include fixed insets, independent coordinate trimming, corner-only
or one-axis removal, canvas-edge removal, first-two survivors, a three-survivor
threshold, retention, filling and a second peel. Query outputs never affect
which rivals survive demonstrations. These are finite Python rival checks
against Racket-checked labels, not a proof against arbitrary programs.

Native source inventory and qualification use the repository's existing API:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 17ea562973ac \
  --evidence generators/17ea562973ac/workspace/parametric/evidence/current \
  --include generators/17ea562973ac/tests/test_parametric.py \
  --reported-checks 'Focused protected-Racket evidence; see the current receipt'
python3 review.py run python3 -m arcpuzzles parametric qualify 17ea562973ac \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/17ea562973ac/qualification-new --summary
python3 review.py run python3 \
  generators/17ea562973ac/workspace/parametric/verify.py witness \
  --qualification ../checks/17ea562973ac/qualification-new/qualification.json \
  --out ../checks/17ea562973ac/sequential-witness-new.json
```

An existing manifest requires its exact current SHA-256 via `--replace`.
The witness contains two executed skip-A counterfactuals using the original
canonical rule and the qualified peeling program on the same inputs.

## Public projection and handoff

`public_view(episode, query_index=0)` returns only demonstrations and one current
query input. It contains no settings, seed, reference program, query answer,
future query or total-count hint. The first view is byte-identical for one-query
and four-query requests. The controller keeps the complete private episode and
reveals each later view only after the preceding answer; this adapter does not
implement a new turn controller. Public filenames hash the exact bytes from
`reviewer_support.public_challenge_bytes` and are independent of private fields.

Native qualification is reviewer evidence. After integrating these exact files,
the owner must freshly qualify and accept the live bytes through the native API.
No acceptance record is created by this prototype, and no training data is
admitted by its tests, examples, inventory or qualification.
