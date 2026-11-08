# Horizontal dominoes after color grouping

This is a separate native parametric proposal for `e46c2557ad08`. The ordinary
generator and its canonical Racket authority retain their original bytes.
Reviewer qualification is evidence for owner intake; only fresh native
acceptance on the integrated source enables the variants. No training admission
or mixture change is requested.

## Design and implementation plan

The original reasoning is to identify monochromatic connected objects, compare
their exact shape with a horizontal domino, and recolor qualifying gray objects
cyan. The private episode field keeps its legacy name `preprocess`, with three rule choices:

| Value | Executed behavior |
|---|---|
| `none` (canonical default) | Execute the exact original Racket program. |
| `blue_to_gray` | Change blue (1) to gray (5), recompute connected objects, then execute the original shape-selection body on that intermediate grid. |
| `nearest_vertical` | Locate the unique original vertical gray domino, then recolor only its uniquely nearest original horizontal gray domino, using minimum Manhattan cell distance. |

The input-dependent intermediate matters. A gray/blue horizontal pair becomes a
new gray domino; an original gray domino touching a blue extension becomes a
longer object and stops qualifying. Choosing the targets before merging is
wrong. Both effects are taught in the first demonstration and retained in a
small executed counterfactual witness.

An orientation-only parameter would be meaningful but would not add the required
dependency. Applying a color mapping only after selecting objects would be a
cosmetic change. Recomputing connectivity after the mapping preserves the core
reasoning and makes the new operation causal.

The implementation sequence is deliberately bounded:

1. Write tests for the exact default, creation/destruction witnesses, request
   validation, independent counts, deterministic matched inputs, and real 30×30
   content; observe the missing implementation fail.
2. Implement one standard-library prototype, a thin adjacent-file adapter, and
   a native promotion contract. Keep the claimed Python labels separate from
   their later protected-Racket verification.
3. Audit demonstrations against finite, executable rivals; repair any witnessed
   shortcut. Execute minimum/maximum count requests and the four size profiles.
4. Freeze the source/evidence inventory, run native qualification, and derive
   the public examples, first-turn check and causal witness from those exact
   qualified bytes. Return the source delta and compact evidence.

## Input grammar and teaching

The **separate prototype** broadens the input grammar to black (0), blue (1),
green (3), and gray (5), with 4-neighbor monochromatic components. The ordinary
all-gray generator does not acquire this grammar. The canonical Racket program
already has defined behavior on these colored grids; its default text remains
byte-for-byte identical. All three settings use the same input sampler, so rule
differences are taught by output labels rather than by setting-specific geometry.

Every episode begins with a constructive pair of demonstrations. Together they
include created and destroyed dominoes, plain horizontal gray dominoes and a unique vertical gray
anchor, a longer gray run, a mixed-color square, blue and green dominoes, a
gray domino touching green, and a diagonal contact. These teach exact shape,
orientation, color selection, order
of operations and 4-neighbor connectivity. Further examples add translated,
reflected and more numerous arrangements. Reflections preserve the horizontal
rule; quarter-turn rotations are not a supported augmentation.

`generate(seed, settings, demos, queries)` accepts **2–6 demos** and **1–4
queries**, independently, with **3 demos / 4 queries** as the ordinary request.
The first-query evaluation projection is supported without changing its content.
Input random streams depend on seed, split and pair index, never the private
setting or requested totals. Increasing a count preserves existing input
prefixes. All returned inputs must be distinct, with strict integer grids.

Four query profiles are 12×15, 16×20, 24×26, and 30×30.
Demo profiles are 12×16, 14×18, 16×22, 18×24, 22×26 and 26×28.
The common grammar retains exactly one vertical gray anchor, at least two
horizontal gray targets and a unique nearest target. A bounded setting-neutral
sampler rejects distance ties. Its first demonstration also distinguishes
Manhattan distance from squared Euclidean/Chebyshev distance and from all four
coordinate extrema, using only setting-neutral structural constraints.
The bounded sampler uses at most 1,024 attempts per scene. The legacy
creation/destruction motifs remain present. The added nearest rule is the exact
reviewer-authored program, not a blue-merge/nearest Cartesian interaction. Larger canvases contain
additional objects distributed throughout the canvas, including boundary
contacts; they are not padded copies. Slots have a one-cell separating gap,
while the colored fragments *within* a motif deliberately touch or meet
diagonally. The explicit `scene` helper now supports **12–30 rows by 15–30
columns**, narrowed from the prior 8–30 by 9–30 helper domain so the common
three-rule teaching grammar fits. This helper is not exposed by the native
adapter: `program(settings)` and `generate(seed, settings, demos, queries)`
retain their interfaces and the independent 2–6 demo / 1–4 query bounds.
No retained task-local tool or regression calls `scene` directly.

## Files and reuse

- `canonical.rkt`: exact selected authority bytes.
- `nearest.rkt`: exact reviewer-authored nearest rule from review-2b9feb332b9b9fc9.
- `nearest-top-left.rkt`: exact authored position-only causal ablation.
- `evidence/merged-final/`: fresh protected audit for this three-rule union.
- `../../tests/test_parametric_union.py`: exact-program, common-grammar, nearest-distance and one-turn projection checks.
- `prototype.py`: request validation, rule materialization, constructive input
  sampling, and explicitly non-authoritative Python output claims.
- `adapter.py`, `promotion.json`: the native interface and bounded contract.
- `audit.py`: a reusable local tool for protected-Racket label/rival checks,
  source-bound causal witnesses, public projection and first-turn equality.
- `evidence/final/`: retained historical two-rule checks; not fresh union verification.
- `evidence/manifest.json`: generated by the repository's native helper.
- `../../tests/test_parameters.py`: focused prototype tests.

The canonical default and both previously accepted Racket texts remain byte-exact.
The prior two-setting input distribution changes to the common grammar;
legacy settings retain their behavior, with independently scheduled matched input
prefixes. `public_turn` emits one selected query input without count/index hints,
future inputs, settings, programs, seeds or query answers.

The audit is finite. Rejecting its named rivals does not prove uniqueness against
all possible programs or measured training benefit. The tile-based sampler also
does not claim to cover arbitrary overlapping objects.

## Reproduce

From the packet's outer directory, after `python review.py setup` and dependency
installation, use the same Python environment for the launcher and payloads:

```sh
WORK/.venv/bin/python review.py run python -m pytest \
  generators/e46c2557ad08/tests/test_parameters.py -q

WORK/.venv/bin/python review.py run python \
  generators/e46c2557ad08/workspace/parametric/audit.py \
  --out generators/e46c2557ad08/workspace/parametric/evidence/final

WORK/.venv/bin/python review.py run python -m arcpuzzles parametric manifest \
  e46c2557ad08 \
  --evidence generators/e46c2557ad08/workspace/parametric/evidence/final \
  --include generators/e46c2557ad08/tests/test_parameters.py \
  --reported-checks 'Use the actual focused-test and audit results for this source'

WORK/.venv/bin/python review.py run python -m arcpuzzles parametric qualify \
  e46c2557ad08 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/e46c2557ad08/qualification

WORK/.venv/bin/python review.py run python \
  generators/e46c2557ad08/workspace/parametric/audit.py \
  --qualification ../checks/e46c2557ad08/qualification/qualification.json \
  --out ../checks/e46c2557ad08/qualified-evidence
```

Use new output paths for reruns; inventories must be deliberately refreshed with
the previous manifest hash after source changes. Exact commands and outcomes
from this return are in `WORK/RESULTS.json`.

Public challenges contain only demonstrations and query inputs, named by hashes
of those public bytes. The four-query file is a controller-side container. The
existing `teammate.make_data.prompt_target` renderer exposes one selected query
per prompt, without a total-count hint; its first prompt is identical to the
single-query projection. Hidden settings, programs, answers and later queries
must remain outside the currently visible prompt.
