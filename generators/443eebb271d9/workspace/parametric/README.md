# Native special-period family — 443eebb271d9

The episode-fixed **special_period** parameter is 3 (exact canonical default)
or 2 (alternative). Every p-th horizontal glyph copy is color 6 and extends
downward. All color-7 cells form one glyph, including disconnected fragments.
Its full bounding box determines both lattice pitches, each with a one-cell
gap. The complete first lattice row appears; other rows contain only selected
columns. Partial copies at the right and bottom edges remain visible.

## Design and API

The thin **adapter.py** loads the adjacent prototype and assigned generator by
exact paths. **canonical.rkt** preserves the canonical program byte-for-byte.
**promotion.json** declares 2–6 demonstrations and 1–4 queries independently.
Ordinary requests use three demonstrations and four queries.

~~~python
program(settings) -> str
generate(seed, settings, demos, queries) -> {
    "train": [{"input": ..., "output": ...}, ...],
    "test": [{"input": ..., "output": ...}, ...],
    "program_solution": ...
}
~~~

Seeds must be literal integers in 0..2**63-1. Invalid settings, extra keys,
coerced scalars and unsupported counts fail closed. The hidden setting is fixed
for the episode; inputs match across settings and demo/query prefixes remain
stable when either count changes. Every input within an episode is distinct.

The retained rule was reused rather than rebuilt. Randomly extending the old
four-input sampler would bypass its connected/disconnected teaching curriculum.
Constructive assembly therefore supplies two essential demo roles:
a disconnected split_corner on 11×18 and an asymmetric stair on 17×23.
The stair starts in column 1 or 2 to expose the sixth instance in a two-demo
lesson. Later demonstrations broaden masks, sizes and origins.

Queries cover 11×18, 30×30, 19×26 and 26×29. The large role varies among 70
constructive shape/origin choices. Sampled protected-Racket outputs occupy
138–214 cells and reach row/column 28 or 29. Sparse inputs are inherent to a
single-source-glyph task; repeated outputs use the large canvas substantively.
Unrelated colored distractors would change this authority's interpretation.

## Teaching repair and dependency

Independent review found a concrete ambiguity in the first native sampler:
seed 2 placed the stair at column 6, so “only the third copy is special” fit
both demonstrations but changed 45 cells of the large query. The original
Racket-labeled lesson and both executable interpretations are retained in
**WORK/checks/443eebb271d9/ambiguity-before-repair.json**.
Moving the stair into columns 1–2 teaches the sixth copy without adding a demo.
The original lesson is research evidence, not multiple official gold answers.

A extracts the whole glyph and computes its full bounding box and mask.
The intermediate is (origin, height, width, mask, width+1, height+1).
B maps output locations into that derived lattice, selects every p-th instance,
and propagates selected columns. A changed pitch changes which spatial columns
B selects. This is input-dependent geometry controlling a subsequent
transformation, not iterative updated-grid simulation.

The source-bound protected witness is packaged under
**WORK/checks/443eebb271d9/causal/**. It substitutes fixed horizontal pitch 3
for the input-derived pitch while retaining the full glyph. Both final outputs
are executed through Racket.

## Reproduce bounded checks

From the outer folder containing review.py, using an interpreter that passes
python-check:

~~~sh
python3 review.py run python3 -m pytest -q \
  generators/443eebb271d9/tests/test_native_special_period.py \
  generators/443eebb271d9/tests/test_parametric_special_period.py \
  generators/443eebb271d9/tests/test_review_repair_443eebb271d9.py

python3 review.py run python3 \
  generators/443eebb271d9/workspace/parametric/build_prototype.py \
  --out-dir generators/443eebb271d9/workspace/parametric/evidence/NEW
~~~

Use a fresh output path. The builder checks both settings, seeds 0/2/17,
demo counts 2/3/6 and four queries: 18 episodes and 138 labels. It executes
13 rivals on six two-demo lessons and checks every supported demo count in a
30-request census. The current result has no demo-fit/query-diverge rival
and no failed request. Focused tests: 52 passed. These are bounded checks,
not universal uniqueness or measured learning benefit.

Current evidence is **evidence/native-final/**. Private files hold executed
episodes, rival programs and minimal witnesses, coverage, and public ID mapping.
The summary records source hashes and runtime identity.

## Public views

The builder emits hash-named single-query files. Names hash exactly the
visible demonstration inputs/outputs and the current query input. Settings,
seeds, programs, query answers, query numbers and total-count hints are absent.
The first turn is byte-identical to a request containing only that first query.

**The controller serves one hash-named file at a time.** The public/ directory
is a staging collection of all precomputed views and must not be given wholesale
to the model. The private/public-map.json file holds ordering and the complete
future-query pool. No training loop or turn controller is added.

Old special-period-v1/special-period-final artifacts are superseded historical
evidence. Their setting-named files are not current public training inputs;
the rewritten builder no longer emits that format.

## Native qualification and owner handoff

Build the guarded inventory with arcpuzzles parametric manifest, then run:

~~~sh
python3 review.py run python3 -m arcpuzzles parametric qualify 443eebb271d9 \
  --seed 0 --seed 2 --seed 17 --demos 3 --queries 4 \
  --out ../checks/443eebb271d9/qualification --summary
~~~

Qualification/execution receipts, source inventory and causal replay are
separate evidence. Reviewer readiness does not grant owner acceptance.
After integration, the owner must qualify and accept exact live bytes through
the native API. No training admission or mixture change is requested.

The aggregate task-tests command still hits the inherited unchanged fixture
tests/test_generator_443eebb271d9.py, whose fixed path looks for canonical data
beneath the task in the portable runtime. This preflight failure is reported
separately; it is not a passing aggregate result. The focused tests above use
the supplied portable helpers.

