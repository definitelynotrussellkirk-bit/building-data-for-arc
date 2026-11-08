# Exact vertical lines with a measured marker

This opt-in prototype preserves the selected canonical program byte-for-byte.
It does not change `generator.py`, the canonical rule, existing approval, or
historical audit dispositions. Owner acceptance of the exact integrated native
source is required before normal parametric generation; no training admission
is implied by this workspace or its reviewer qualification.

## Rules and dependency

| `length_rule` | Eligible blue components |
| --- | --- |
| `fixed_five` (default) | Same-color 4-connected components in one column with exactly five cells; exact canonical program |
| `marker_size` | Same geometry, with length equal to the cell count of the unique color-6 component |

Recolor only each eligible component's middle cell to 2. Preserve every other
cell, including the marker, horizontal blue objects, branched blue objects, and
the color-7 distractor. The generated marker has 3, 5, or 7 occupied cells, so
the selected blue line has an unambiguous middle cell.

**A:** Isolate the unique color-6 component and count its occupied cells.
**Intermediate:** Its input-dependent count `k` and source cell coordinates.
**B:** Select exact vertical blue 4-components of size `k`, then mark their
centers. The set of eligible blue objects cannot be selected until `k` is known.
This is contextual gating through a measured intermediate, not iterative
simulation of an updated grid. The causal witness substitutes the wrong
intermediate `k=5` on qualified inputs with `k=3` and `k=7`; the final outputs
must change under protected Racket execution.

## Sampling and teaching

`generate(seed, settings, demos=3, queries=4)` returns private `train`, `test`,
and exact `program_solution` claims. It accepts exact integer seeds in
`0..2**63-1`, 2–6 demonstrations and 1–4 queries independently. Booleans,
floats, unknown settings and out-of-range requests are rejected. All pair
inputs are distinct. Randomness is local and derived from seed, split and
pair index; counts and private settings do not affect input sampling. Prefixes
therefore remain stable when requesting more examples or queries.

The first two demonstrations use a three-cell L marker and a seven-cell
cross-plus-corners marker. The latter has one interior cell, so occupied-cell
count and boundary-cell count differ before any query needs that distinction.
Both include exact five-cell and marker-length vertical targets,
branches on both kinds of run, horizontal negatives, wrong-length verticals,
and diagonal blue singleton contacts. These contacts preserve true
4-components while refuting an 8-connected interpretation. Markers are
nonrectangular, distinguishing occupied cell count from bounding-box area and
height. Color-7 remains a four-cell distractor. Reflections vary placement
without changing vertical orientation; whole-grid quarter-turns are not used.

| Split | Shapes in stable index order | Marker sizes |
| --- | --- | --- |
| Demonstrations | 14×21, 17×24, 21×27, 24×30, 28×27, 30×30 | 3, 7, 5, 7, 3, 5 |
| Queries | 14×24, 21×27, 30×30, 29×30 | 5, 3, 7, 5 |

The larger grids contain two bands of blue objects with a blank separator,
plus marker and horizontal-negative regions. The 30×30 query has substantive
content in every quadrant and blue boundary contacts, not just enlarged empty
margins. The minimum profile is larger than the canonical 8–10-row examples
because one input carries the two competing length rules and multiple
structural negatives. Production profiles remain unchanged.

The finite audit tests run-only marking, arbitrary-shape marking, all-odd
vertical marking, 8-connectivity, marker bounding-box area, marker height and
marker boundary-cell count,
as well as the other declared parameter setting. A finite-rival pass does not
establish uniqueness against every imaginable rule. Marker roles and sampled
shapes are deliberately bounded; there is no claim to sample every legal ARC
grid or to make color-6 connectivity separately inferable when it is unique.

## Reproduce the checks

Run these commands from the outer packet folder with the passing interpreter.
The wrapper runs payloads inside `WORK/repo`; `../checks` means `WORK/checks`.
Use fresh output directories after source changes.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/7bba59d92716/tests/test_parametric_generator.py \
  generators/7bba59d92716/tests/test_parametric_projection.py

WORK/.venv/bin/python review.py run python3 \
  generators/7bba59d92716/workspace/parametric/audit.py \
  --out ../checks/7bba59d92716/self-audit

WORK/.venv/bin/python review.py task-tests 7bba59d92716 \
  --phase after --out ../checks/7bba59d92716/task-tests
```

`audit.py` is reusable: it executes labels and rival programs through the
same-checkout protected Racket bridge, checks only demonstrations when fitting
rivals, and checks all queries for any surviving rival. It also records a
bounded sampler success rate, geometry and exact source/program hashes.
The audit is separate from `generate`; native generation does not recursively
launch another audit. Python mirrors alone are never qualification evidence.

After all source files and tests are final, copy compact audit/test evidence
into `evidence/current` and build the native inventory:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest 7bba59d92716 \
  --evidence generators/7bba59d92716/workspace/parametric/evidence/current \
  --include generators/7bba59d92716/tests/test_parametric_generator.py \
  --include generators/7bba59d92716/tests/test_parametric_projection.py \
  --reported-checks 'Use the actual bounded audit and isolated task-test results'

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 7bba59d92716 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/7bba59d92716/qualification --summary
```

An existing inventory requires the native explicit `--replace SHA256` guard.
Changing any bound executable/resource source requires a new qualification.
The included causal recipe is built/replayed with `arcpuzzles.review_witness`
against that qualification; its interpretation is reviewer-authored, while
the native helper verifies source identity and both final Racket outputs.

## One query per visible challenge

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/7bba59d92716/workspace/parametric/export_qualified.py \
  --qualification ../checks/7bba59d92716/qualification/qualification.json \
  --out ../checks/7bba59d92716/projection

WORK/.venv/bin/python WORK/check_public_exports.py \
  WORK/checks/7bba59d92716/projection/public --queries 1 --demos 3
```

The reusable exporter validates the existing native qualification/execution
digest, program map, current source and protected-runtime receipt through the
native verifier. It then emits `public/<visible-sha256>.json`, containing the
demonstrations and exactly one query input. Settings, seeds, programs, answers,
query order and future query inputs stay in `private/manifest.json`. The first
view is byte-identical to the single-query projection. The consumer must reveal
one file only after the prior answer; do not give the public directory listing
or private manifest to the model. No total-count/final-turn hint is in a view.

This tool serializes verified reviewer evidence; it does not replay Racket,
authenticate maliciously rewritten evidence, accept the family, or implement
a turn controller. Existing destinations and duplicate visible payloads fail
closed. After integration, the owner must run fresh native qualification and
acceptance on the live source before using the ordinary accepted-family API.
