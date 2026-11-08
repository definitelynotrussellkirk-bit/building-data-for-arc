# Working notes: a55c1997c5e3

## Current review — native tie-order parametric family, 2026-10-24

Assignment `review-7558014547ea824f` leaves the approved canonical generator
byte-for-byte unchanged at SHA-256
`195743d1f77b6928ded4de8eabf5d6ebb27434b46a11c52cd895547219147779`
and rule hash `d24e861b64b5`. A task-local native prototype now fixes one of
two direction-priority orders for an entire episode: the canonical
right/down/left/up order or the counterfactual up/left/down/right order. The
canonical Racket program remains exactly SHA-256
`7df9c720e4680c082d5eaf20392716962ea04688cbbc8a418a5addcfc31931a3`;
the alternate changes only the direction-rank block.

The adapter accepts 2–6 demonstrations and exactly four queries. Inputs are
matched across settings, the first two demonstrations leave exactly one of all
24 constant direction orders consistent, and the query set includes a genuine
30-by-30 border-spanning case. Evidence includes 75/75 staged task tests,
28/28 protected-Racket labels matching the independent Python mirror, four
canonical public projections passing the scoped export checker, native
qualification at 2, 3, and 6 demonstrations, and a source-bound sequential
counterfactual witness. See `workspace/parametric/evidence/manifest.json` and
`checks/a55c1997c5e3/` in the returned packet.

Limits and next action: this establishes only the two shipped settings and a
finite audit of the 24 constant direction orders. Native status is
reviewer-reported; owner integration, fresh acceptance replay, canonical
approval, and any training admission remain pending. The assignment's public
authoring focus `3e6067c3` is marked `inspired_extension` with an unverified
relationship, so no direct lineage claim is made.


## Current repair — strict recipe identity boundary, 2026-10-24

Assignment `review-400900fb9684fbbd` extends the public-call validation without
changing version `2.2.1`, sampling, curriculum, canonical data, or Racket code.
`generate` now accepts only exact Python integers for `seed` and exact
nonnegative Python integers for `sample_index`; booleans, floats, strings, and
`None` seeds are rejected before `gen_ctx`, while signed integer seeds remain
valid and deterministic.

Current generator SHA-256:
`195743d1f77b6928ded4de8eabf5d6ebb27434b46a11c52cd895547219147779`.
Selected canonical rule hash remains `d24e861b64b5`.

Evidence: 42/42 staged task tests passed; the cross-target scalar probe rejects
all probed invalid seed/index classes; four fixed valid calls are
byte-identical to the pre-change grids; and 4/4 bounded canonical Racket outputs
match `_official_python_mirror`. See
`checks/final-verification-summary.json`,
`checks/valid-output-invariance/comparison.json`, and
`checks/racket-parity/comparison.json`.

Remaining scope: this repair makes no new claim about the existing path
curriculum or broader semantic completeness; those behaviors were deliberately
left unchanged.


## Current repair — version 2.2.1, 2026-10-12

Review assignment `review-aa34ac6179575d74`. The selected Racket rule and canonical
data are unchanged. The rule connects the longest simple path by **node count**
from the red 2-by-2 square, resolving equal-length paths by their complete
right/down/left/up direction sequence. Geometric distance is not the objective.

Final generator SHA-256:
`b6bb38a232161349a61673014767ff5c2a769101ff0c3c3aa04dd67723f44e76`.
Baseline version 2.1.0 SHA-256:
`1931ca006f1e4d78adb47ad16a96899d1e347c85313103cdc98d0b8e63a5929e`.
Imported associated notes retain their original timestamps and evidence in
`evidence/associated_notes.jsonl`; those historical claims are not new checks.

## Defects and changes

- **R1 — incorrect canonical-shortcut declarations.** The six old declarations
  each contradicted at least one labeled canonical pair. They remain useful
  lesson competitors, but only five demonstrated canonical-fitting alternatives
  are now in `CANONICAL_SHORTCUTS`: three upward-priority permutations, an
  endpoint-based tie resolver, and a shortest-distance tie resolver. All five
  fit all five usable canonical pairs, including the labeled test pair.
- **R2 — incomplete teaching support.** The original five shapes never
  distinguished the three upward-priority alternatives. Its four-demo schedule
  also admitted an endpoint rival that fit a normal demonstration window but
  changed its query. A new twelve-node `complete_direction_order` shape provides
  all three adjacent direction-priority comparisons in one label; the original
  five topologies remain available.
- **R3 — invalid scalar inputs (extended 2026-10-24).** Reject non-exact-integer
  seeds plus boolean, non-integer, and negative `sample_index` values before
  constructing the generation context. Signed integer seeds and override
  behavior are preserved.
- **R4 — geometric shortcuts in an intermediate repair.** Explicitly challenge
  shortest distance, greatest physical distance, greatest painted area, and
  greatest distance among maximum-node paths. Two local gap inequalities make
  the intended path alternately shorter or longer than tied alternatives.
  Other legal coordinates, margins, and dimensions remain sampled.

## Curriculum contract

`EXAMPLES_NEEDED = 6`; `LESSON_SCHEDULE_PERIOD = 10`. The cyclic schedule is:

```
complete_direction_order, tie_down_over_left, longest_over_priority,
complete_direction_order, tie_down_over_left, deep_lexicographic_tie,
complete_direction_order, tie_down_over_left, branchy_unique_longest,
tie_right_over_down
```

Any seven consecutive schedule slots contain at least two complete-direction
examples, two endpoint/longer-distance examples, and two length-before-greedy
examples. Holding out any one slot preserves each category. This supports six
demonstrations plus one query, including any held-out query position with the
remaining order preserved. It is not a promise about arbitrary subsets of six
examples. `scene_profile` selects one of six unique shapes; `schedule_profile`
describes one of ten slots. Exact height/width controls remain 16–28 / 18–30.

The executable lesson hook evaluates the actual declared competitors and the
required witnesses. There are 34 named competitor identities, including all 23
incorrect total direction orders. This is not a claim of 34 behaviorally
distinct rules: the pre-existing reversed-order competitor has an equivalent
permutation entry.

## Evidence and reproducible tools

The return's `checks/after-final/` records a 12/12 green strict battery, including
the fixed-period receipt and required query rotations. `checks/task-tests-ready/`
records all 35 task tests passing in an isolated staged runtime, with zero skips.
The initial missing-pytest prerequisite failure is separately retained.

`checks/lesson-census-final.summary.json` records 300 materialized lessons,
2,100 labeled pairs, 2,100 query rotations, and 2,073 exact unique inputs across
three bands. No declared-rival ambiguity, hook warning, or scoring/materializing
error was found. Requested starts are 0–99 per band; seeds follow the public
census's recorded deterministic SHA-256 recipe, not a claimed consecutive seed
range. `checks/schedule-census-final.summary.json` covers all ten cyclic starts
at seed 0 in each band: 30 lessons, 210 rotations, 36 unique inputs, no findings.
The raw censuses are retained as native gzip reports with hash/restore manifests.

`workspace/probe_path_curriculum.py` separates preparation, public Racket apply,
and scoring. It discovers actual declarations, preserves rival predictions,
verifies canonical fit, checks generated counterexamples, and binds receipts to
source hashes. Its representative windows reuse inputs; use the public census
for production evidence. `counterexamples/` contains compact verified fixtures.
Task tests use public portable root/canonical helpers. Fast curriculum tests
use the Python mirror; the battery, probe, and census supply Racket authority.

## Limits and future work

This remains a deliberately finite six-topology generator. It does not cover
all lawful graphs, every possible rival, or unrestricted demonstration assembly.
Constrained gaps counter specific metric shortcuts; they do not prove that no
coordinate-based heuristic exists. The finite census supports the declared
competitors and tested sampler only. Difficulty bands share the semantic
curriculum. Six demonstrations cost more context than four, but no tested
four-demo replacement established the desired rotation coverage. No generator
approval or training admission is claimed.
## Current reviewer considerations

Source SHA-256: `b6bb38a232161349a61673014767ff5c2a769101ff0c3c3aa04dd67723f44e76`.

# Repair decisions

Assignment: `review-aa34ac6179575d74`; selected task `a55c1997c5e3`.
Final generator: version 2.2.1, SHA-256
`b6bb38a232161349a61673014767ff5c2a769101ff0c3c3aa04dd67723f44e76`.
The canonical row, Racket authority, and both audit targets were not changed.

## R1: Make the executable declarations truthful

The before battery passed ten stages but failed defect lint and the semantic
gate. The old `CANONICAL_SHORTCUTS` mapped six tempting heuristics that each
failed at least one canonical label. Canonical-fit status is an empirical
contract, not a synonym for a plausible mistake. I retained those heuristics in
`LESSON_COMPETITORS` and declared only five alternatives whose predictions match
all five labeled canonical pairs. The regression checks every actual callable
against every usable canonical pair, rather than maintaining a second name list.

Evidence: `checks/before/`, `checks/contract-tests-before/`, and the canonical-fit
tables in `checks/path-curriculum-final/scored.json`. The before tests recorded
nine failures and eleven passes; the failures were retained and then repaired.

## R2: Change teaching support, not merely the validation hook

Three canonical-fit rivals agree with every original graph topology while
changing the priority of up. Stretching coordinates cannot distinguish these
rules because they depend only on graph directions. A new twelve-node shape
forces right over down, down over left, and left over up along competing maximum
paths. One label refutes every incorrect total ordering of the four directions.
The original five shape controls remain available for variety and compatibility.

The endpoint rival is stronger evidence of a practical lesson defect: on the
original-shape seed-0 medium window, demonstrations with sample indices 3–6 fit
that rival and sample 7 changes its answer, even though the old hook returned no
reason. The reference labels were obtained through public Racket apply. That
probe used an intermediate source with scalar/declaration edits but the original
shapes and schedule; it is explicitly labeled intermediate, not baseline bytes.
See `checks/path-analysis/scored.json`, `prepared.json`, and `racket.json`.

Increasing `EXAMPLES_NEEDED` from four to six is a substantive cost. The ten-slot
cycle supplies redundancy for three categories of discriminating evidence: the
new complete-direction shape, endpoint/longer-distance discrimination, and
length-before-greedy discrimination. Each category occurs at least twice in any
seven-slot window, so removing any one query leaves a demonstration witness.
Keeping four examples with the existing schedule left demonstrated ambiguity;
merely relaxing the hook or making query rotations advisory would conceal it.
I selected six demonstrations and explicitly required the rotation checks.

The supported assembly is six demonstrations plus one query from seven
consecutive accepted samples, with every query position tested and the remaining
order retained. The public production census also exercises materialization and
records accepted indices; symbolic reuse of six shape representatives is a
separate diagnostic. The post-repair solve contains six demonstrations and two
unlabeled queries; its execution record is not a private correctness score.

## R3: Validate scalar input at the API boundary

Python booleans are integer subclasses. The original generator accepted `True`,
`False`, and negative sample indices. Validate a nonnegative, non-boolean integer
before `gen_ctx`. The red tests demonstrate this boundary independently of the
curriculum tests. Existing exact size/profile controls, determinism, canonical
agreement, malformed-grid checks, and purity tests remain in the task suite.

## R4: Retain the physical-distance failure and fix its cause

An intermediate 2.2.0 candidate could still teach maximizing physical distance,
painted cells, or physical distance after node count. On seed 0, easy, sample
indices 0–6, holding out position 4 left all three rivals consistent with the six
demonstrations and wrong on the query. All seven labels were confirmed by Racket
on source `37d464d061d20bc23b50b71688e37057b2d8d36ee80759d19fa1730048471aec`.
See `checks/path-analysis/distance-scored.json` and `checks/metric-support-before/`.

The final generator constrains two local gap comparisons. In the complete-order
shape, the official equal-node path is physically longer than its shortest-route
alternative. In `tie_down_over_left`, the alternative ending left is physically
longer than the official right endpoint. Thus neither minimizing nor maximizing
distance explains the whole lesson. Other gaps and translations are sampled.
The added three maximization rivals are lesson competitors, not falsely labeled
canonical-fit shortcuts. A separate read-only code review checked the gap bounds
over every supported height/width combination.

## Verification decisions and retained failed attempts

The final strict battery is 12/12 green. A preliminary after battery on the
intermediate source was 11/12 green, with an explicit warning that its declared
ten-slot period had not been enumerated. I preserved it in `checks/after/`, ran
the required fixed-seed period census, and supplied the exact receipt to the
final battery in `checks/after-final/`.

The isolated task-test stage initially ran no tests because pytest existed only
in the user site, which that stage correctly disables. An offline venv now has
pytest and its pure Python dependencies installed locally, while using the
runtime's NumPy and Pillow. The normal isolation remains enabled; all 35 tests
pass with zero skips. Both the prerequisite failure and a first environment
installation iteration are retained. Environment setup and replay instructions
are in `checks/environment/`.

Full censuses are native gzip reports with original size/hash manifests. One
redundant decompressed schedule report was removed only after byte-for-byte
comparison with both its gzip content and the final battery's retained input.
The exact raw receipt remains in `checks/after-final/checks/schedule-census-input.json`.
No sole failure copy was removed. `checks/schedule-census-retention.json` records
the decision and restoration mapping.

## Self-review and limits

The sixth topology and gap inequalities strengthen the tested discrimination but
also restrict the distribution. A solver could memorize six graph families, and
the declared rivals are not an exhaustive hypothesis class. The final 300-lesson
census covers three bands, requested starts 0–99 and deterministic hashed seeds;
the period census covers every residue at only seed 0. Neither is a universal
proof. The consecutive-slot coverage argument alone does not certify a lesson
if duplicate rejection changes its accepted indices; the production census and
executable hook assess the actual materialized bundles. There are 34 named competitor identities, not 34 necessarily distinct
behaviors; namespace aliases and a reverse-order equivalent are documented.

Audits A1 (`22f494053811`) and A2 (`5383f0933057`) are source-bound findings only.
Their exact Racket-verified examples and owner repair suggestions are in
`AUDIT.md`; neither audit source is included in the repair patch. No approval,
training admission, or private solve correctness is asserted by this return.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a55c1997c5e3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
