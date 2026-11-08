# Blue-object ranking by cells or bounding-box area

**Status: proposed prototype.** The selected production generator and canonical
Racket authority are unchanged. This folder adds a native promotion adapter,
a deterministic sampler, Racket-backed examples, and a replay verifier. It does
not accept the variants or admit data to training.

## Rule and supported requests

Choose `metric` once per episode:

| Setting | Score of each blue component |
| --- | --- |
| `cells` (canonical default) | Number of occupied cells |
| `bbox_area` | Height × width of its bounding box, including empty cells |

Find exactly three blue, four-connected objects. Sort by the selected score,
then by top row and left column for ties. Recolor the ordered objects 2, 3, 8.
Preserve every non-blue cell. The default program is **byte-for-byte identical**
to the selected canonical program; the alternative replaces only the two score
expressions. The reference remains Racket for both settings.

`adapter.generate(seed, settings, demos, queries)` supports **2–6 demonstrations
and 1–4 queries independently**. The example CLI defaults to three demonstrations
and four queries. Counts, sizes, and seeds reject boolean and fractional values;
seed range is 0 through `2**63 - 1`. No short or duplicate episode is returned.
The adapter's labels are Python claims until the native protected worker checks
them. `generate_episode` and the CLI execute both metric programs on every pair.

## Teaching and sampling

The first two demonstrations constructively distinguish the metric and its
tie-breaking rule, while changing the same T tetromino's output color under
both settings:

| Demonstration | Objects, listed as occupied cells / bbox area | Distinction |
| --- | --- | --- |
| First | T4 4/6, L5 5/8, rectangle 6/6 | The T4 is above/right of the rectangle: row priority defeats column priority; the L5 changes rank between metrics. |
| Second | L3 3/4, T4 4/6, P5 5/6 | T4 and P5 share a top row; P5 is left of T4. This teaches column priority and reverses the size/tie correlation. |

The certificate fits **fourteen declared rules using demonstrations only**:
the two settings, reverse score orders, spatial orders, identity, distractor
erasure, and five bbox tie shortcuts. It also refutes any fixed per-object
size-to-color or rotation/reflection-invariant shape-to-color lookup. Query
answers and private settings are excluded before fitting. This is a finite
teaching check, not universal uniqueness against arbitrary programs.

Input RNG streams do not depend on the metric. The same seed and counts give
identical inputs across settings. Demonstration and query streams are separate;
changing one count does not change the prefix of the other split. Spatial
teaching candidates have a hard limit of 32; the retained bounded probe reports
actual attempts and failures rather than concealing rejected requests.

The four ordinary query shapes are **10×12, 16×20, 24×24, 30×30**. Additional
demonstrations use 10×12 through 18×18. The general sampler accepts exact height
and width from 10 through 30, including rectangular extremes. It grows three
connected polyominoes with variable density, large bounding boxes, and border
contacts, adds preserved distractors, then applies a D4 orientation. Objects
occupy separate bands before orientation; the family does not cover every legal
placement or interlocking object geometry. Large examples contain larger objects,
not a small scene surrounded by empty padding. Bbox ties remain supported and
are taught; they are not filtered away.

The first two teaching examples deliberately preserve their absolute row/column
tie arrangements while varying positions, object orientations and distractors.
Global rotation of tied scenes can change tie outcomes; labels are always
recomputed from the transformed grid, not rotated from the old answer.

## Run from the review packet's outer directory

Activate the packet-local environment prepared according to `START-HERE.md`.
Use a new output directory for each invocation.

```bash
python3 review.py run python3 \
  generators/8118155d8959/workspace/parametric/prototype.py build \
  --seed 17 --demos 3 --queries 4 --metric all \
  --out ../checks/rank-metric-examples

python3 review.py run python3 \
  generators/8118155d8959/workspace/parametric/prototype.py verify \
  ../checks/rank-metric-examples

python3 review.py run python3 \
  generators/8118155d8959/workspace/parametric/probe.py \
  --out ../checks/rank-metric-probe.json

python3 review.py run python3 -m pytest -q \
  generators/8118155d8959/tests/test_parametric_rank_metric.py
```

`probe.py` records 30 bounded episode requests, matched-input checks, live
Racket parity at 10×10, 10×30, 30×10 and 30×30, and all eight D4 transformations
of the retained tied-area query. It keeps counts, source hashes and exact runtime
identity, including failures. It is a scoped authoring probe, not a full battery.

## Public projection and replay

The writer emits hash-named `public/` challenge files, corresponding `private/`
records and a sorted public index. Public IDs hash exactly the visible bytes
written by `reviewer_support.public_challenge_bytes`. Settings, seed, program,
query answers and certificates remain private. Hidden fields cannot change the
public name. Duplicates and existing output paths are refused before publication.

**A four-query public file is a controller-side challenge bank.** Give the model
`first_turn(episode)`, which contains the demonstrations and only the first query.
It is byte-equivalent in content to a one-query request with the same seed and
demo count. For later turns the existing consumer reveals only the next query
input after the preceding answer. Do not expose the bank index, its full-payload
ID, future inputs, query count, or a final-turn marker. No turn controller or
training loop is added here.

The verifier checks exact public bytes, exact file and directory inventories,
strict integer grids including private outputs, unique inputs, source/program
bindings, protected runtime identity, and a recomputed demonstration-only
certificate. It freshly executes both Racket programs on every retained pair.
Editable hashes or claims in a receipt cannot substitute for label replay.
Verification binds the current source/runtime; a source or runtime update needs
fresh evidence. This is not cryptographic authentication of an untrusted bundle.

## Native owner qualification

`promotion.json` declares the finite settings and bounds. The native
`parametric manifest` inventory binds these files and retained evidence; it does
not execute the adapter. Qualification independently checks the adapter against
the exact canonical default and both programs through protected Racket:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 8118155d8959 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out generators/8118155d8959/workspace/parametric/evidence/qualification
```

Owner acceptance is a separate action. Training allocation, measured learning
benefit and trajectory admission remain downstream decisions.
