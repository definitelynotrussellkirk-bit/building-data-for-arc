# Working notes: 0ee358bd9d75

## Canonical rule and domain

Full-zero rows and columns divide the input into rectangular sections. Emit one
cell per section, in the same arrangement, containing its unique most frequent
nonzero color. Zero is background/divider material; color numbers have no rank
semantics. `RULE_HASH=bd52339e94ff` and the canonical program are unchanged.

The generator keeps 8..30 rows/columns, 1..3 nonadjacent internal divider rows
and columns, section sides at least two cells, both painted and zero cells in
every section, nonempty local rows/columns, and a unique nonzero mode. Exact
controls remain observable. Invalid scalar types, nonfinite density, and
infeasible joint controls fail explicitly; errors name the incompatible axes.

## Review repair: version 3.0.0

The prior random style mixture allowed a first-nonzero selector to fit all three
demonstrations and fail the query: a raw scan found 19/300 such lessons, and
the easy seed 6 production lesson was confirmed with Racket. A prior unresolved
audit, `review-d3b87882f505f62c:v0001`, was used as a lead, not as proof of this
source's behavior. Its review-index state remains for maintainer resolution.

Default draws now repeat a three-position schedule: a complete canonical-profile
anchor, then two mixed-color frequency witnesses. Every four consecutive pairs
therefore contain at least two witnesses, so holding out any one query leaves
a demonstration that rejects each declared first/last/minimum/maximum/rarest
selector. `EXAMPLES_NEEDED=3`; arbitrary shuffling of those four pairs is covered,
but arbitrary resampling or dropping additional demonstrations is not.

Within mixed draws, separate sections put a minority color at the first and
last nonzero scan positions using count-preserving swaps. Every section has a
unique dominant color, and output palettes vary independently of numeric rank.
The first candidate retained a roughly 20% minority budget and caused excessive
color fragmentation (native component median 50 versus canonical 15). It was
reversed to a default-only budget `max(1, painted//12)`, bounded below the mode;
the first/last witnesses remain. Explicit diagnostic noise overrides keep their
broader budget. Regression evidence covers seeds 1..100 and50001..50100 in all
three bands; final medians37 and 38 remain above the canonical median without
exceeding the existing distribution threshold. This is not morphology equality.

Two selected base-solution `racket_target.target_code` strings are synchronized
to the canonical text. The canonical ledger and archival `raw_code` are
unchanged. This is an exact-text authority repair, not a rule change.

## Verification and limits

Review `review-b6772c0d4b458307` retains the failures and final evidence. Final
generator SHA-256 is
`4a8bc307fc9fb6c1470c528b7dc6c285391636c1b5e11818f3a11a26d0ede26b`.
The complete after battery passed 12/12 stages; portable task tests passed 28
tests and55 subtests. A production census materialized300 lessons/1200 unique
inputs and checked 1200 query holdouts with no ambiguity against the five
declared rivals. Fixed seed 0 covered all three schedule starts in each band:
9 lessons,36 holdouts,14 unique inputs. Evidence is in the return's
`checks/after-final/`, `checks/task-tests-final/`, `checks/lesson-census-final.json`
and `checks/schedule-census-final.json`.

This is a finite rival check, not universal identifiability or measured model
mastery. The default sampler makes winners absolute majorities; it does not
cover every lawful unique plurality, frequency tie, or unrestricted divider
layout. Diagnostic overrides do not promise the default teaching schedule.
Periodic anchors and sparse minorities are deliberate distribution restrictions.

## Current native parametric handoff

Review `review-cd777f9486ae8026` upgrades the existing section-frequency prototype
to native **qualified / owner acceptance pending**. The canonical generator and
both most/least-frequency Racket programs retain their exact bytes. The thin
adapter and promotion contract expose independent 2–6 demonstrations and 1–4
queries, with three demonstrations recommended. The source-bound inventory is
`workspace/parametric/evidence/manifest.json`.

The old sampler's three-demonstration contract had no observed failure against
the finite tested selectors. Extending it to two demonstrations without a
teaching repair would expose last-cell seed 306 and first-cell seed 413 shortcuts.
The revised setting-independent pool rejects those shortcuts and numeric
minimum/maximum/opposite-frequency rivals under both settings before choosing
demonstrations. Each emitted demonstration is a witness. Independent streams
preserve prefixes across count changes; no demonstration selection borrows query
answers. The 8×8 minimum and substantive 30×30 first query are ordinary profiles,
with mixed content and nonzero local row/column coverage throughout the canvas.

The bounded independent after-probe completed 35/35 pools: 350 accepted inputs
from 389 candidates, maximum 5 candidates per input and no exhausted sampler.
It covered 40 count requests at the two regression seeds and 38 Racket labels.
The input filter still has a 256-candidate cap per position and may fail on
unexercised seeds; it raises instead of silently shortening an episode. The
checks establish only the declared finite rival family, not universal uniqueness.

Both live writers now use exact visible-byte hash filenames and private
program/metadata directories. `public_turn` exposes only the current query;
the first turn is byte-identical for one-query and four-query use. A controller
must advance after each answer. Hidden settings, answers, and future inputs do
not affect the first-turn bytes or identifier.

Native qualification passed both settings on seeds 0 and 17 with 3 demos and 4
queries: 4 jobs, 28 checked pair labels and 40 protected-Racket evaluations.
`checks/0ee358bd9d75/qualification/{qualification,execution}.json` retains that
execution. Focused prototype/count tests passed 18 tests plus 12 subtests
(session-reported); the causal helper's 4 tests and actual replay also passed.
Canonical compatibility remains covered by the focused prototype tests; no
unchanged production battery was rerun.

The causal dependency is inferred divider positions → section membership →
section-local frequency selection. `verify_causal.py` binds the exact qualified
source and executes both original and wrong-bound programs. On its lawful 8×8
case, replacing divider row 2 with 5 changes `[[1,5],[5,7]]` to `[[5,7],[5,7]]`.
Both outputs are 2×2, and one original 5 changes while another does not, excluding
a fixed output-color remap. This is input-dependent grouping, not evidence of
iterative updated-grid simulation. The source-bound witness is
`checks/0ee358bd9d75/causal-witness.json`.

Next owner action: integrate this exact delta, qualify the integrated bytes, and
perform native acceptance with the retained causal witness. This reviewer return
does not create acceptance or admit training data. Older evidence and discussion
below retain their own source scope; current commands are in the prototype README.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d3b87882f505f62c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b8046ad4a9d614a5d4e8f4dff721edcee64986d3c91efa4d8459c83233315ac4`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve first-nonzero lesson shortcut: canonical anchors plus two frequency witnesses in period3 teach frequency and defeat the old rival; reviewer28 tests+55 subtests,300 lessons/1200 rotations and all period3 starts pass. Current source 4a8bc307fc9fb6c1470c528b7dc6c285391636c1b5e11818f3a11a26d0ede26b. Evidence remains reviewer-reported and finite; no universal or training-admission claim.

### Assessment or prior finding

## 0ee358bd9d75

**Reproduced lesson-level shortcut.** Generator SHA-256
`b8046ad4a9d614a5d4e8f4dff721edcee64986d3c91efa4d8459c83233315ac4`
allows a wrong rule to emit the first row-major nonzero cell from each section
instead of the uniquely most-frequent nonzero color. The generator has a focused
test showing that some hard sample refutes this rule, but no production schedule
guarantees such a witness inside each lesson.

Across seeds `0..999`, sample indices `0..4`, the rival fit every demonstration
in:

- 502/1000 easy lessons;
- 214/1000 medium lessons; and
- 69/1000 hard lessons.

The concrete authoritative reproducer is `difficulty=easy`, seed `0`. All five
generated inputs pass the task's self-check, and all five authoritative Racket
outputs exactly equal the first-cell rival.

- Consolidated finding: `checks/audit/0ee358bd9d75/counterexample.json`
- Production inputs: `checks/audit/0ee358bd9d75/input.json`
- Authoritative outputs: `checks/audit/0ee358bd9d75/racket.json`
- Rival outputs: `checks/audit/0ee358bd9d75/rival.json`
- Reproducible scan: `checks/audit/scan_lesson_rivals.py` and
  `checks/audit/scan_lesson_rivals.json`

`arcpuzzles apply` executed rule hash `bd52339e94ff`, matched the catalog hash,
and accepted all five outputs. This is a production-lesson identifiability issue,
not an authority mismatch. No patch was made because this is an audit-only
target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d3b87882f505f62c-v0001/audit_assets.json), manifest SHA-256 `845a0d807d3c5b7adb63fec626108074db957b5081fb90f9717d73682bbc3205`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `4a8bc307fc9fb6c1470c528b7dc6c285391636c1b5e11818f3a11a26d0ede26b`.

# Decisions for review-b6772c0d4b458307

## Preserve the canonical problem

The core computation remains zero-divider partitioning followed by per-section
nonzero frequency and compact placement. Canonical rule hash`bd52339e94ff`, exact
program SHA`06116072ebc0f8b09c3a8bfb876b9816b688280bdacf5d66e8944d2bf6825f7f`,
and full canonical ledger SHA`9d46eb627dac0d3f096b8b1a63dd95e012039cf72d0d08f3d1bbbc109211965f`
remain unchanged. Both selected base target strings now match that authority;
archival raw_code remains untouched. Changing the rule to justify weak lessons
was rejected because the defect was in teaching support, not reference semantics.

## Parametric priority

The prototype was developed in parallel with canonical diagnosis, in its own
task workspace. One binary semantic parameter was sufficient: choose the unique
most frequent or least frequent present nonzero color. It preserves section
roles, counting, coordinates, background handling and output arrangement. A
second cosmetic parameter was rejected because it would not add a new rule.

The canonical default uses literal catalog Racket bytes; the alternative changes
one comparator. Inputs are sampled independently of the setting. Both extrema
must be unique, and generated sections contain two or three colors, so each
demonstration distinguishes the settings. This deliberately excludes ties and
does not extend production approval. Seeds0..7 and50000..50007 test both settings
and four holdouts; full public/private episodes and executed programs are retained.

## Teaching schedule and demonstration count

The imported generator randomly mixed monochrome and noisy sections; its
original rationale is unknown. A first-cell rival fits every canonical example
because each canonical section is single-color. The reproduced easy-seed 6
production lesson leaves it alive across all three demonstrations but contradicts
it on the query. Merely adding more noisy support probabilistically would leave
that event possible, and one witness per four pairs would disappear under a
permitted query rotation.

The chosen period 3 is canonical anchor, mixed witness, mixed witness. With three
demonstrations and one query, every consecutive window of four contains at least
two mixed inputs. Each mixed input refutes all five declared rivals. Any single
query holdout therefore retains a witness; ordering among those four pairs is
irrelevant. This is a bounded contract, not a guarantee for independently
resampled pairs, arbitrary overrides, fewer demonstrations or undeclared rules.

Complete linked canonical profiles preserve shapes, section dimensions and color
equality patterns, with random palette/occupancy variation. Independent marginal
height/width/color matching alone was rejected as insufficient canonical support.
Default canonical anchors occupy one schedule residue. Explicit controls remain
exact and opt out of that default schedule rather than being silently ignored.

## Witness construction and morphology reversal

Within noisy sections, retain a unique dominant color and minority marks. Swap
colors to make the first nonzero wrong in one section and the last wrong in a
different section. Swaps preserve occupancy and counts; using different sections
works even when a small section has only one minority cell. The emitted output
palette and mixed accents also distinguish numeric minimum/maximum and rarity.

The first candidate reused the inherited 20% accent budget at two-thirds of default
draws. That over-fragmented colors: native median 50 components versus canonical 15.
We retained the failure and wrote a failing morphology regression. Independent
comparison of 1/8,1/12 and a fixed2-cell cap favored1/12: it preserves size scaling
and had medians37/38 across seeds 1..100 and50001..50100 in all bands. The default
budget is now `min(max(1,painted//12),(painted-1)//2)`; explicit noisy controls keep
their previous range. Final battery passes. Sparse hard inputs can still be very
fragmented; this correction does not assert canonical morphology equivalence.

## Controls, tests and environment

Reject coercion for seeds, indices and integer axes; reject boolean/string density,
nonfinite values and unsupported difficulty. Feasible boundaries remain8 and30.
Infeasible joint geometry/color requests raise ValueError with actual incompatible
axes. Existing task-local tests were portable-migrated through public helpers,
preserving their assertions; no frozen root fixture was changed.

System Python lacked isolated pytest, and the first task-test run recorded an
infrastructure failure. An independent virtual environment supplied numpy 2.5.4,
Pillow 13.0.0 and pytest 9.1.1. Network-restricted installation initially failed;
the approved installation succeeded. No gate was weakened, skipped or relabeled.

## Scope of evidence and decisions left to maintainers

Before, intermediate and final results have separate paths and hashes. The
300-lesson production census and all 1200 single-query holdouts bind the final
generator. Fixed seed 0 additionally covers every finite schedule start, not all
random seeds. The post-repair solve is explicitly exposed; both solves leave
masked-query labels unknown. Audit targets are findings-only. Prior review-index
closure, generator admission and proposed parameter approval remain maintainer
decisions; the patch does not alter their status.

## Fresh handoff replay

Use the public declared runtime dependency closure to avoid unpacking another
full 103,281-file archive; this is explicitly partial repository scope. The
closure contains 343 original files and supports the selected task's public
runtime and focused tests. All 17 patched paths were checked after actual Git
application. A newly created venv with the pinned dependencies and a separate
offline Racket setup passed the same 28 task tests plus 55 subtests; post-test
hashes still match the original final workspace.

The first helper used `review.py check`, which requires an assignment file not
present in the fresh runtime closure. That attempt failed before tests ran and
is preserved. The fixed helper calls `review.py run PYTHON -m arcpuzzles check
TASK_ID` with the task ID from the replay receipt. It never reconstructs a draw,
weakens a gate, borrows the original venv, or edits source to make the test pass.
