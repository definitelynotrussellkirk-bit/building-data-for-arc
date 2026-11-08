# Proposed rotation/scale extension

This task-local family now has a native promotion adapter and finite contract.
Its original family is `training:2b9ef948`, selected generator `5e8e4691afde`.
The adapter remains reviewer-ready rather than owner-accepted: it does not alter
the canonical generator, canonical rule, allocation weights, or training admission.

The native API supports 2–6 demonstrations and exactly four queries.  The older
standalone authoring CLI remains available for retained evidence and permits wider
counts, but those wider counts are outside `promotion.json` and are not admitted.

## Rule and bounded parameters

Find the colored center of the color-4 3×3 frame, the same-color indicator at
one end of the gray path, and the extra color-4 endpoint. Let `(dr, dc)` be the
endpoint minus the indicator. Transform that displacement, move the frame's
center by it, fill the output with its original center color, and draw the
color-4 frame and both full diagonals through the new center. The center itself
keeps its color.

| Parameter | Allowed values | Default | Meaning |
|---|---|---|---|
| `quarter_turns` | `0, 1, 2, 3` | `0` | Clockwise quarter turns of the displacement; one turn sends `(dr, dc)` to `(dc, -dr)` in row/column coordinates. |
| `distance_scale` | `1, 2` | `1` | Multiply both components of the rotated displacement by this integer. |

The eight hypotheses change the executed translation, while object roles,
endpoint binding, background fill, frame, and diagonal construction stay the
same. At `(0, 1)`, `program_for()` returns the **exact selected canonical Racket
text**; its SHA-256 is
`ae926b19ad08aa049ff2ef63cb8f0ea0f43d56185cdc6429d7b581ba405687d8`.
Other settings replace only the two displacement-to-center definitions. All
eight exact programs are materialized in each export's private program folder.

Parameters remain fixed for every demonstration and query of an episode.
Explicit controls select them once; `--sample-settings` draws one setting from
the deterministic episode seed. With no setting controls, the default is the
original `(0, 1)`. `--all-settings` creates an episode for every setting and
uses the same input sampling recipe across settings, so layout cannot encode
the hidden setting. `--count` is the number of episodes **per setting** in that
mode. An episode index gives each subsequent episode a separate deterministic
layout and, when requested, a separate seeded parameter draw.

## Native promotion contract

`adapter.py` exposes `program(settings)` and
`generate(seed, settings, demos, queries)`.  `promotion.json` declares all eight
Cartesian settings, the exact canonical default `(quarter_turns=0,
distance_scale=1)`, 2–6 demonstrations, and exactly four queries.  Inputs are
matched across settings for a fixed seed.  Native qualification independently
re-executes every declared Racket rule on demonstration labels, requires the
selected rule to be the sole survivor, and then checks all query labels.

`self_audit.py` adds a bounded demonstration-only check against all eight
settings plus copy, solid-fill, original-center, endpoint-center,
indicator-center, frame-only, diagonal-only, and retain-background shortcuts.
It is finite evidence, not a universal uniqueness proof.

## Exact four-query commands

From the outer extracted packet directory, with its Racket setup complete:

```bash
python3 review.py run python3 generators/5e8e4691afde/workspace/parametric/prototype.py --seed 17 --all-settings --demos 3 --queries 4 --out ../checks/parametric/episodes
```

This writes eight complete episodes: 24 demonstration pairs and 32 query
targets. The original setting and the alternative `(1, 2)` also have a common
lawful input and their two executed outputs in `private/difference_witness.json`.

For only the original setting, use a new output location:

```bash
python3 review.py run python3 generators/5e8e4691afde/workspace/parametric/prototype.py --seed 19 --demos 2 --queries 4 --out ../checks/parametric/additional-export
```

For a particular alternative, `--quarter-turns 1 --distance-scale 2` selects it.
For deterministic hidden parameter draws, use `--sample-settings --count 2`.
These setting controls are mutually exclusive with `--all-settings` and
`--sample-settings`. All public artifacts are under an opaque-name `public/`
folder; export folder names must also omit settings and seeds when shared.

If an installed Racket is already on `PATH`, the equivalent command can run
directly from `WORK/repo/` without the packet wrapper. The prototype bootstraps
only that checkout's `shared/runtime/` imports. It requires the repository's
Racket prelude and standard Python libraries; pytest is unnecessary.

## Teaching, dimensions, and bounded sampling

Demonstration and query counts are independent (`--demos`, default 3;
`--queries`, default 4; each permits 1–32). Inputs within an episode are all
distinct. The sampler varies positions, center colors, signed path vectors,
path bend order, and rectangular dimensions. Demonstrations are 16–20 cells
on each side. Every fourth query, starting with the first, is exactly 30×30
with a longer path vector; other queries have 21–29 rows and columns. Thus
each query is larger than every demonstration in both dimensions. Larger
outputs draw the diagonals all the way to their grid boundaries.

The source frame and all eight possible translated frames fit inside every
sampled grid. The gray path avoids their footprints. This deliberate common
domain makes identifiability depend on demonstration outputs rather than an
alternative's out-of-bounds behavior. The canonical five examples remain
supported by the default program and are tested separately; they need not be
lawful at every alternative setting.

`sample_inputs()` has one total draw budget per episode (`--max-attempts`,
default 4096, maximum 100000). It records accepted attempt numbers, rejections,
dimensions, and input hashes. Failure raises `SamplingError`; counts are never
silently shortened. Seed and episode index, all counts, and both parameters
require exact bounded integers, rejecting booleans and coercible strings in
the Python API. The CLI rejects bad controls before starting Racket or writing.

Candidate fitting receives **demonstration pairs only**. The Python geometry
mirror is a filtering cross-check. Each of the eight Racket programs is also
executed on those demonstrations; the prototype requires exactly one survivor.
It then executes the survivor on each query input and retains a separate
per-query uniqueness certificate. Query labels never participate in fitting.
Actual Racket labels are checked against the geometry mirror. A persistent
protected bridge and a cache keyed by exact program/input hashes avoid repeated
execution of identical requests; no Python label is exported as Racket evidence.

## Public and private output

Only `public/` is a model-visible challenge set. Each file is exactly
`reviewer_support.public_challenge_bytes(episode)`, named
`<public_challenge_id(episode)>.json`. Files are created in sorted content-ID
order. That projection contains demonstration inputs/outputs and query inputs
only. The private manifest, setting map, seed, query answers, exact Racket
programs, source hashes, runtime identity, and difference witness live under
`private/`. Changing private metadata or query answers cannot change a public
filename. Duplicate visible payloads are rejected before an export is created,
even when their private metadata differs. Existing destinations are rejected.

`private/manifest.json` records the invoked payload command, all eight program
hashes, source hashes, program/input execution counts, canonical-default checks,
and explicit limits. Its `public_ids` and episode records are sorted by public
content ID, independent of the order settings were generated. Public filenames
do not contain settings, seeds, or setting-associated ordinals.

## Focused verification

From the outer packet directory:

```bash
python3 review.py run python3 -m unittest discover -s generators/5e8e4691afde/tests -p test_parametric.py -v
```

These tests cover only the prototype: invalid controls; finite rejection;
deterministic, fresh, distinct inputs; all-eight-setting frame bounds;
demonstration-only identifiability; the five canonical outputs through exact
default Racket; executed episodes at every setting; independent demo/query
counts; and public writer identity, ordering, isolation, and duplicate checks.
This is not a production battery. Retained execution evidence belongs under
`WORK/checks/parametric/`; no broad model or curriculum claim follows from it.

The finite rival set excludes other possible ARC rules. Sampled paths are
straight or have one Manhattan bend; the canonical winding paths are covered
only by canonical-default tests. The all-settings common domain intentionally
omits legal single-setting layouts near a boundary. These are documented limits
of the proposed sampler, not claims that the broader family is exhausted.
