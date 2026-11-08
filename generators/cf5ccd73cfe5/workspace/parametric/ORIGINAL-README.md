# Frame-and-marker orientation: native promotion candidate

One episode-fixed `orientation` parameter has four values: `identity` (exact
canonical default), `flip_lr`, `flip_ud`, and `rot180`. The reviewed canonical
program detects a hollow frame, aggregates the entire separate marker color,
measures its bounding box, and independently repeats rows and columns into the
frame interior. Alternatives change only the marker-coordinate membership
lookup. Frame roles, binary shape, colors and separate axis scales are preserved.
Quarter-turns are outside this rule domain because they exchange marker axes.
The canonical production generator and exact reference remain unchanged.

## Native interface and reproduction

`adapter.py` loads the exact adjacent `orientation.py` by path. Its strict API
exports `program(settings)` and `generate(seed, settings, demos, queries)`.
Settings must name exactly `orientation`; seeds are exact integers 0..2**63-1.
The promotion contract supports **2–6 demos and 1–4 queries independently**,
with three demonstrations for qualification. Labels are executed by Racket in
the shared prototype and re-executed independently by native qualification.

From the outer packet directory, with the prepared Python interpreter:

```bash
WORK/.venv/bin/python review.py run python3 generators/cf5ccd73cfe5/workspace/parametric/orientation.py --seed 17 --demos 3 --queries 4 --out ../checks/cf5ccd73cfe5/examples
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/cf5ccd73cfe5/tests/test_native_orientation.py generators/cf5ccd73cfe5/tests/test_parametric_orientation.py
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify cf5ccd73cfe5 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/cf5ccd73cfe5/qualification --summary
```

The output directories must be new. Build the current source manifest first as
specified in `docs/parametric-promotion.md`; the returned inventory and evidence
are already supplied. The low-level `build_episode` keeps its legacy one-query
default for existing callers; the CLI defaults to four, and the native API takes
an explicit independent count. Native qualification is not owner acceptance.
The owner must qualify and accept the exact integrated source before using it.

## Sampling, teaching and real size variation

The input stream is independent of the hidden orientation. Demonstrations use
the existing canonical sampler. The first **accepted** demo must distinguish
all four orientations and reject eight plausible shortcuts under each of four
orientations: fixed red border, fixed 3x3 marker, height-only uniform scaling,
square output, largest 8-connected marker component, solid fill, periodic tiling,
and unscaled copying. This is 32 explicit Python rival predictions tested against
Racket gold. The other three orientations are executed Racket competitors.
The retained per-episode certificate checks demonstrations only before assessing
query disagreement. Its finite rival set does not prove universal identifiability.

All accepted inputs are distinct, and each has four distinct orientation outputs.
Symmetric or otherwise insufficient teaching draws are rejected within a shared
256-attempt budget. Exhaustion raises with actual rejection details; the chosen
rule is never resampled. Query inputs have their own deterministic stream, so
requesting one or four leaves the demonstrations and first query identical.

Four query profiles (randomly transposed/reflected) are 8x8, 18x24, 24x30 and
30x30. Their frames are respectively 4x5, 14x22, 20x27 and 26x26, so size stress
changes actual replicated content rather than adding empty borders. The largest
has a 3x6 or 6x3 marker and repetition factors 8 and 4; occupied content reaches
all four canvas edges. Markers retain exact bounding boxes with varying sparse
and dense patterns, including disconnected parts. No unrelated-color distractors
are added because the canonical grammar aggregates every non-frame colored cell.
This separate query extension does not alter production's 8..26 axis contract.

## Causal dependency

A identifies the frame and complete marker bounding boxes, then measures the
frame interior and marker dimensions. Its input-dependent intermediate is the
pair of integer factors `(interior_h / marker_h, interior_w / marker_w)`.
B uses those factors to choose which marker row and column supplies every output
cell. The factors cannot be fixed before the two object geometries are known.
A wrong-intermediate witness substitutes the height factor for the width factor;
a second collapses the measured marker height to one. Protected Racket must show
different valid final grids. See the return's `checks/cf5ccd73cfe5/causal/`.
Reflection itself commutes with replication, so it is not presented as an
order-dependent step. This is a measured-geometry dependency, not iterative
simulation, and the reviewer argument is bounded by its actual witnesses.

## Visibility and sequential reveal

Public filenames are the full SHA-256 of **exact `public_challenge_bytes`** plus
`.json`. Private seed, settings, program, query answers and setting enumeration
cannot change an otherwise identical visible file or its name. Batch files are
written in public-ID order and duplicate visible challenges fail. Private
receipts contain the executed programs, answers, rejection details and settings.
Retained older `final-s17-release` files document the previous prototype and are
not current export examples: their old names included private seeds.

The four-query challenge is a controller-side bank. On each user turn expose
only the fixed demonstrations and the current query, using the existing helper:

```python
public_challenge_bytes({"train": episode["train"],
                        "test": [{"input": episode["test"][query_index]["input"]}]})
```

Keep future queries, answers, private metadata, total query count and final-turn
hints outside model input. The first-turn byte regression compares this projection
with a separately requested one-query lesson. No training loop or turn controller
is implemented here. No training admission or measured learning gain is claimed.
