# Proposed occluded rectangles family

This is a separate, opt-in research prototype inspired by the public visible
examples of evaluation task `a6f40cea`. It does not modify or replace canonical
family `3f26d45b9f51`, its generator, its Racket authority, or approval metadata.
It is not a general evaluation-task solver and no hidden evaluation answers were
read. The two families have substantially different object roles and dependencies.

## Mechanism and bounded grammar

Each input has an exterior context color, one rear **solid-color rectangular
outline**, one larger opaque foreground frame, and one unrelated small frame.
The foreground border is a color role, varied randomly rather than tied to 3.
Its strict interior has one uniform fill color, which can equal the exterior
context or be a distinct color. The small 3x3 frame uses the foreground border
color and lies outside the main crop.

The main frame is found from the input: connected monochrome components must
bound a complete rectangular border of at least 5x5 with a uniform interior of
a different color. The largest qualifying frame wins; equal-area ties reject.
The generator makes the rear rectangle cross two neighboring frame sides. All
four rear extrema survive somewhere outside the occluder. Recover the rear
bounding box from those surviving pixels, reconstruct it inside the strict
frame interior, and crop out the foreground border and exterior. The background
of the output is the foreground **interior fill**, not the exterior context.
Horizontal and vertical reflections vary which two sides the rear object crosses.

The renderer samples board dimensions 22..26, main frame dimensions 7..10,
position, palette, rear offsets, context/fill equality and reflections. Different
colors identify the one rear rectangle uniquely. The prototype excludes overlapping
rear objects, several rear palettes, clipped rear extrema, ambiguous foreground
frames, frame/rear palette collisions, and arbitrary shapes. Its pixel parser
is designed for this emitted grammar; it is not an exhaustive validator of every
possible ARC grid matching part of that description.

## Episode parameter and inference

`paint` is fixed once per episode:

- `outline` (default): paint only the hidden rear rectangle perimeter.
- `filled`: paint the entire rear rectangle portion within the crop.

Inputs always show the same kind of rear outline. Thus the parameter is learned
from demonstration input/output pairs. It is not passed in a public query or
encoded in the input palette. Every generated geometry has hidden rear area and
remaining crop background, so its demonstration separates these two settings.
Changing `n_train` does not change the default **four** query count.

`certify(demonstrations)` accepts only demonstration pairs. It enumerates both
parameter settings and the named `visible_only`, `drop_crop`, and
`always_full_crop` rivals. It retains the unique parameter and rejects those
rivals before an episode is returned. No query or query answer enters that
certificate. This finite certificate does not establish unique induction against
all possible programs.

`context_witness()` supplies two inputs with identical entire opaque frame
interiors but different surviving rear left sides. Their outputs differ for
both paint settings. This checks the intended dependency on exterior evidence;
a crop-only shortcut cannot solve even this bounded family.

## Controls and failure behavior

`generate_episode(seed=0, paint='outline', n_train=2, n_queries=4,
max_attempts=128)` uses exact integers (booleans, strings and floats reject).
The demonstration and query counts are each bounded to 1..16 and the global
attempt budget to 1..4096. A seed is any exact integer. Exhausting the budget
raises rather than returning a short episode. All full input grids are distinct
within an episode. Batch export additionally rejects repeated input grids
across episodes, even when different demonstration labels give different IDs.

## Racket labels and public boundary

The sibling `occluded_rectangles.rkt` independently discovers the frame and rear
geometry from each input and executes the requested painting rule. Generation
runs this actual Racket program in one bounded standalone subprocess per episode,
then checks every returned label against the Python pixel parser. No labels are
silently replaced by Python when Racket is missing. The standalone process is
used because this new, small rule does not depend on the canonical ARC DSL or
its prelude; it does not invoke or alter a canonical authority.

Runtime resolution is explicit `RACKET_PATH`, then this packet's
`WORK/.review/racket-runtime/racket/bin/racket`, then `racket` on `PATH`.
`subprocess.run` has a 30-second timeout. The verification environment sets
`TMPDIR=WORK/checks/occluded/tmp`.

`export_batch` uses the repository's `reviewer_support.public_challenge_bytes`
and `public_challenge_id` directly. It sorts rows by the SHA-256 of exactly the
visible challenge bytes and rejects duplicate visible IDs before creating the
output directory. Files under `public/` contain demonstration pairs and query
inputs only. Query answers, the seed, the painting parameter, the rule hash,
and the finite certificate go under separate `private/` files. The batch
manifest contains IDs and portable paths relative to its own folder, with
`canonical_equivalence: false`.

Before writing any export files, every episode is checked against the current
rule hash, exact seed/paint/count/budget/attempt metadata, exact integer labels,
deterministically regenerated input sequence, recomputed demonstration-only
certificate, and freshly executed Racket demonstration/query labels. Certificate
and label comparisons use canonical JSON, so booleans cannot masquerade as integer
values. Counts are matched to visible pairs, and attempt metadata must reproduce
the input stream. A larger valid retry budget can reproduce the same stream;
validation checks its consistency, not an unavailable external history of which
budget a caller originally supplied.

`verify_export(path)` and `--verify PATH` repeat those checks on a saved export.
They also recompute the exact public bytes and visible IDs, enforce sorted unique
IDs and relative paths, reject repeated inputs and unexpected files, and reject
path escapes. The verifier accepts at most 64 episodes and reads at most 2 MiB
per JSON file. The exporter likewise accepts 1..64 episodes.

Example, from `WORK/repo`:

```sh
TMPDIR=../checks/occluded/tmp python generators/3f26d45b9f51/workspace/parametric/occluded_rectangles.py --seed 500 --paint outline --n-train 2 --n-queries 4 --max-attempts 128 --out ../checks/occluded/example-new
```

Verify the saved batch, including after moving its entire folder:

```sh
TMPDIR=../checks/occluded/tmp python generators/3f26d45b9f51/workspace/parametric/occluded_rectangles.py --verify ../checks/occluded/example-new
```

Output paths must be new. Save or share only the intended public directory when
constructing a challenge-only dataset; the parent export folder also has private
labels and its manifest.

## Why alternating colors are excluded

The first two public evaluation demonstrations support ordinary rear rectangular
outline completion. The third uses two-color outlines, but a global checkerboard
continuation is inconsistent with its visible output in one rectangle: exposed
input `(13,15)=9`, `(13,16)=8`, `(16,7)=8`, `(17,7)=9` implies hidden
`(13,7)=9` under global parity, while the demonstration output at crop coordinate
`(5,1)` is 8. Coordinates are zero-based. No hidden answer was consulted to
resolve that discrepancy. Alternation therefore needs a separately specified
phase/turn convention or a documented annotation exception. This prototype
claims only the unambiguous solid-color geometric mechanism, and its filled
setting is an authored extension rather than a demonstrated evaluation rule.

## Verification evidence

From `WORK/repo`:

```sh
TMPDIR=../checks/occluded/tmp python -m unittest discover -s generators/3f26d45b9f51/tests -p test_occluded_rectangles.py -v
```

`WORK/checks/occluded/` retains initial and regression test-first failures,
the final ten-test green log `tdd-green-export-validation.log`, current source
hashes and verification results in `result.json`, current public/private examples
in `sample_batch_v2/`, and the private context witness. The current focused tests
exercise actual Racket replay, both painting settings, one-demo/four-query
lessons, demo-only certification, exact controls, retry exhaustion, context
dependence, tampered private metadata/labels/certificates, rejection before writes,
portable export relocation, canonical public bytes, independent CLI query/budget
controls, and CLI verification.

The original 16-episode matrix (31 demonstrations, 64 queries) remains under
`sample_batch/` and `result-before-export-validation.json` as evidence for the
previous source snapshot. That older exporter did not validate private metadata
and used absolute paths. These older examples are not current exports and do
not satisfy the new verifier's metadata schema. The original geometric/rule
matrix is not claimed as a rerun of the revised exporter. The current small
roundtrip uses two newly generated episodes, one per painting setting, and four
queries per episode. All evidence is bounded and reproducible; it does not
confer safety approval or training-data admission.

The repository's full `python -m pytest` command was attempted, but this packet
runtime does not have pytest installed (`No module named pytest`). No full-suite
success is claimed. The extracted packet also has no accessible Git repository;
`git status --short` reports that it is not a Git repository.
