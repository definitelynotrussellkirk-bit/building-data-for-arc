# Native spiral-direction family

This adapter promotes the retained `spiral_direction.py` prototype without
rewriting either rule. `clockwise` is the exact selected canonical program;
`counterclockwise` is the retained alternative. Both locate the gray U, count
wholly empty rows strictly between its walls and above its floor, then paint
that many positions of a 3×3 cyan spiral, saturating at nine. Both start at the
top-left cell. Colors 0/5/8 retain their fixed semantic roles.

## Native API and sampling

`adapter.program(settings)` and `adapter.generate(seed, settings, demos, queries)`
use settings `{"spiral_direction":"clockwise"}` or
`{"spiral_direction":"counterclockwise"}`. A setting is fixed for the episode.
Seeds must be exact integers in 0..2**63−1; requests support **3–6 demonstrations
and 1–4 queries independently**. Invalid types, booleans, unknown settings and
out-of-range counts fail rather than being coerced.

Inputs are shared across settings and use separate seed/slot RNGs. Their prefixes
are unchanged when demo/query counts change. Every requested input is distinct,
results are fresh lists, and the sampler never touches global random state.
Bounded duplicate retries fail explicitly instead of returning a short episode.

The three required teaching slots are constructive:

| Slot | Row structure | What it teaches |
| --- | --- | --- |
| 1 | No entirely empty row; six partial rows arranged as three complementary pairs, including singleton cyan at both interior edges | Zero output despite many black cells; exact interior columns; rejects area/column counts and forced minimum outputs |
| 2 | Five empty rows and one complementary pair; first and last interior rows are empty | Unsaturated count, traversal direction, strict row endpoints, and a different area/column correction |
| 3 | Nine to twelve empty rows above solid bottom fill | Full spiral and saturation; rejects premature caps, including the demonstrated cap-six shortcut |

Additional demos vary height, width, row placement and partial masks. The teaching
scaffold deliberately restricts the first three shapes/count regimes. The fixed
semantic colors and finite 3×3 output space also limit diversity; they preserve
the source task rather than making a palette-only variant.

Four queries cover compact zero/one endpoints, medium count-eight/saturated
endpoints, large unsaturated counts, and a **full 30×30 U with a 29×28 interior
and an unsaturated count 2–7**. The last query keeps direction and exact counting
observable while spreading substantial gray/cyan content over the whole canvas.
Output remains 3×3 because that is the rule's count encoding. The new sampler
extends production's ordinary size range; `generator.py` and its controls remain
unchanged. The grammar is an upright U with arbitrary interior 0/8 masks, at
least one cyan cell, and no cyan or extra gray outside it.

## Sequential dependency and repaired teaching gap

A recovers the gray bounds, examines every strict-interior row, and computes
its empty-row set/count. B uses that count to choose the spiral prefix. Moving
one cyan cell into an empty row can change the output while preserving the
entire color histogram. The focused regression executes that 5→4 example.
The native causal witness uses zero-area/width as a wrong intermediate; partial
rows make it differ from the true row count and change the executed answer.

Independent review found a cap-six rule fitting the first draft's three demos
but disagreeing on an eight-cell query. The exact pre-repair lesson and both
protected programs/answers are retained in
`checks/c1ae510562f9/cap-six-original-lesson.json`. The final 0/5/9+ schedule fixes
that demonstrated gap and adds cap/floor rivals. Three demos are now the minimum;
two cannot expose every distinction this teaching construction requires.

## Reusable audit and public views

Run from the packet's outer directory with its independent Python/Racket setup:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q   generators/c1ae510562f9/tests/test_native_adapter.py   generators/c1ae510562f9/tests/test_native_audit.py   generators/c1ae510562f9/tests/test_parametric_spiral_direction.py

WORK/.venv/bin/python review.py run python3 -B   generators/c1ae510562f9/workspace/parametric/audit.py   --seed 0 --seed 17 --out ../checks/c1ae510562f9/audit-new
```

The audit independently labels the selected pairs through protected Racket and
screens all named rivals on the **three demonstrations only**. Only survivors
need query comparison. Execution errors are failures, never refutations. Rivals
cover alternate direction, area/column counts and fixed corrections, any-zero
rows, headroom, span, crop boundaries, longest run, premature caps, forced output
floors, row-major order and snake order. Reports bind source/runtime hashes,
retain actual programs, distinguish logical comparisons from cached evaluations,
and state finite limits. The output directory must be new or empty.

`public_turn(episode, index)` copies the demonstrations plus one query input.
It contains no private setting, seed, program, answer, future input, index,
query-count or final-turn hint. With fixed demos/seed/setting, the first turn is
identical for one-query and four-query use. It is a projection; the existing
consumer controls sequential reveal after each answer.

The audit exports canonical visible bytes to hash-named files under `public/`,
sorted by public ID, and keeps answers/programs/provenance in `private.json`.
Its reusable verifier checks strict fields, typed grids, hashes, public/private
projection, duplicate inputs, and exact inventory/index coverage. Tests reject
leaked fields, forged IDs, private-label tampering and unindexed public files.
Serialized verification is not a fresh Racket replay or authentication of an
entirely rewritten bundle. This copied utility imports only this checkout.

## Qualification and boundaries

After the native source inventory is current:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify   c1ae510562f9 --seed 0 --seed 17 --demos 3 --queries 4   --out ../checks/c1ae510562f9/qualification-new --summary
```

The adapter reuses the original module's exact programs and deterministic claim
mirror; it performs no nested Racket audit during generation. Native qualification
independently checks every label and the finite setting distinction. The original
five-fixture CLI and retained evidence remain historical compatibility/provenance;
the current native API uses the new sampler and strict public projection.

Finite tests and rivals establish neither universal identifiability nor
all-seed correctness or a training gain. Qualification means reviewer readiness.
The owner must qualify and accept the exact integrated source before using the
native accepted-family API. No owner acceptance or training admission is made
by this prototype or its audit.
