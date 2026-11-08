# Current native handoff — 021fb6acf24f

Assignment: `review-b4578108054756aa`. Reviewer disposition: **native ready;
exact-source owner acceptance pending**. Training admission remains false.

Production source is unchanged at generator SHA-256
`28f506566dcff22268a0cac1006e265277c141dc3860c2efc2591264c8801f09`,
canonical `RULE_HASH` `9a7f76b1ea86`, and canonical/default Racket SHA-256
`f7b49e9ffb4c0dcaa332d46e67bd1f4d5c9be35200705fc34f394548380bcbb3`.
The earlier `color_order` prototype is now promoted to a native task-local
adapter without altering those production bytes.

## Native deliverable

`workspace/parametric/adapter.py` implements the declared
`arcpuzzles-parametric-adapter-v1` contract. The episode-fixed parameter is
`color_order = ascending|descending`; `ascending` is the exact canonical
default, while `descending` reverses only the Racket color-processing list.
The adapter independently supports 2–6 demonstrations and 1–4 queries. Query
inputs use a fixed post-demonstration profile offset, so the first query is
independent of requested query count and includes a substantive 30×30 overlap
contest. Inputs are setting-independent and deterministic for a seed/count pair.

The first two demonstrations deliberately reverse which numeric color appears
first in row-major order. This preserves the actual numeric-order lesson while
preventing the plausible “first color seen” shortcut from fitting both examples.
The retained bounded audit executes both settings, two demonstrations, four
queries, and four named rivals through protected Racket: opposite numeric order,
row-major first occurrence, original-zero late overwrite, and identity. All four
rivals fail visible demonstrations and disagree on at least one query. The audit
is finite and is not a universal uniqueness proof.

## Required sequential dependency

A: process the first color selected by `color_order` and fill every still-zero
cell in its input-defined bounding box. The intermediate is the complete grid
after that fill, including claimed overlap cells. B: process the second color
and fill only cells still zero in that intermediate. Because B tests zero-ness
in the accumulated grid, its mask and the final overlap winner cannot be chosen
before A's input-dependent result. Four protected-Racket wrong-order witnesses
cover both settings, including a 30×30 query; final outputs differ by 24, 54,
755, and 335 cells. The owner-like replay executed all eight chosen and
counterfactual labels successfully.

## Retained checks and next action

- Focused native contract: 29/29 passed.
- Full selected-task suite: 129/129 passed in 20.75 seconds.
- Bounded adversarial audit: pass, 60 protected-Racket evaluations.
- Native qualification: four jobs (two settings × seeds 0 and 17), 40
  protected-Racket evaluations, four distinct queries per job, matched inputs
  across settings, and a dense 30×30 query.
- Source inventory manifest SHA-256:
  `5e943afce57ad1876cdeaa203514131f71e57f7896528c120892df9c950fefce`.

Owner next action: integrate the returned delta, re-bind the exact live source,
run native qualification and the fresh protected-Racket witness replay, then
accept only if those exact bytes remain current. This reviewer handoff does not
activate or admit training data. Optional peers `12a886996b14` and
`156db8fda1bb` were left unrun after completing MAIN.

---

# Retained prior account — 021fb6acf24f

Generator version: **3.0.1**. Final source SHA-256:
`28f506566dcff22268a0cac1006e265277c141dc3860c2efc2591264c8801f09`.
Canonical `RULE_HASH`: `9a7f76b1ea86`; canonical Racket source SHA-256:
`f7b49e9ffb4c0dcaa332d46e67bd1f4d5c9be35200705fc34f394548380bcbb3`.
The canonical rule and authority were not edited in assignment
`review-3cb1f29e96c9df42`.

## Intended rule and domain

A zero-background grid contains one or two nonzero colors. Each color has exactly
two anchors in distinct rows and columns. Process colors in ascending numeric
order; for each color, fill only cells that are still zero inside the inclusive
anchor bounding box. Lower colors therefore keep contested overlap cells.
Production dimensions are 6..10 rows by 8..11 columns. A deterministic five-step
profile schedule covers the canonical size/color-count profiles; difficulty
changes geometry, not semantics or public profile.

## Current repair

The previous public API accepted Boolean/non-integer `seed` and `sample_index`
values and allowed negative sample indices through Python negative indexing.
Both `generate` and `schedule_profile` now require plain integers and a
nonnegative sample index before any indexing or RNG construction. Negative
integer seeds remain valid and deterministic. Regression coverage is in
`tests/test_public_scalars.py`.

No distribution, rule, profile, axis, or lesson changes were made. The final
source-bound battery is 12/12 green and the portable selected-task suite is 98/98
green. Profile floor is 60/60 exact and envelope support. A 300-lesson census
(three demonstrations plus one query) and all 1,200 single-query rotations found
no ambiguity against the declared scan-order, late-overwrite, and identity
rivals; a fixed-seed enumeration of all five schedule starts across three bands
also passed 15 lessons / 60 rotations.

## Shortcut witness

`counterexamples/scan-order-overlap.json` is a lawful input where row-major
first-occurrence order and late overwrite disagree with ascending numeric
zero-only filling. Every two-color production draw contains the same structural
contest; three of every five schedule positions are two-color profiles.

## Proposed parametric extension

`workspace/parametric/` contains a runnable **proposed/unapproved** episode-level
`color_order` extension with `ascending` (canonical/default) and `descending`.
It reverses exactly the canonical Racket color-list expression while preserving
objects, bounding boxes, and zero-only writes. Two complete three-demo/one-query
episodes cover both settings; exact Racket evidence checks all eight query
rotations with no ambiguity. This prototype is separate from production and does
not alter approval or authority.

## Limits and open findings

The deterministic schedule is a learnable nuisance prior. Rival evidence is
finite and does not prove unique induction against every possible program. The
supported manifold does not claim extra anchors, nonzero backgrounds, degenerate
boxes, or more than two colors. Passing review does not admit generated data to
training. The post-repair solve passed all three visible examples with honest
earlier exposure; hidden-query correctness remains unscored here.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. The twelve focused naming/writer checks passed across six tasks. This correction does not approve the prototype or rerun its full repair battery.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d926a855c2b55e54:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7b0eb3ea02b7fddc1dae08a1dfff5681820e6fc3f9314a2139257fed614d82b4`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve seed/index coercion and negative indexing: strict pre-draw validators in generate and schedule_profile; reviewer98 tests including new public-scalar regressions and12/12 battery pass. Current source 28f506566dcff22268a0cac1006e265277c141dc3860c2efc2591264c8801f09. Evidence remains reviewer-reported and finite; no universal or training-admission claim.

### Assessment or prior finding

## 021fb6acf24f

**Classification: reproduced generator API defect; audited source unchanged.** The audited generator SHA-256 is `7b0eb3ea02b7fddc1dae08a1dfff5681820e6fc3f9314a2139257fed614d82b4`.

The public request boundary accepts values that should not name schedule positions. `generate(seed=0, sample_index=-1, difficulty="easy")` succeeds and selects the final schedule entry through Python negative indexing instead of rejecting the request. `sample_index=True` and `seed=True` are also accepted because Boolean values are subclasses of `int`. The exact accepted grids, profiles, shapes, self-check results, and hashes are retained in `checks/audit/021fb6acf24f/strict-scalar/evidence.json`; `probe.py` and `probe.log` reproduce the calls.

The existing portable suite passed 51/51 (`checks/audit/021fb6acf24f/task-tests/result.json`), so this is an uncovered contract defect rather than a known failing fixture. Strict defect lint independently failed on the negative-index case (`checks/audit/021fb6acf24f/defect-lint/result.json`).

**Suggested repair:** require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` before any profile selection or indexing; add regressions for Boolean, float, and negative values. I did not edit this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d926a855c2b55e54-v0001/audit_assets.json), manifest SHA-256 `e308f15cbebd9fa710d1f692088dac6019eb2164ab9fa54a7daf04a43ba5e27f`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `28f506566dcff22268a0cac1006e265277c141dc3860c2efc2591264c8801f09`.

# Decisions — 021fb6acf24f

Assignment: `review-3cb1f29e96c9df42`. Final generator SHA-256:
`28f506566dcff22268a0cac1006e265277c141dc3860c2efc2591264c8801f09`.

## D1 — Enforce a strict public scalar contract

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, and
`sample_index >= 0` in both `generate` and `schedule_profile`. Keep negative
integer seeds legal.

**Reason.** The accepted unresolved finding and the baseline `defect_lint` showed
24 violations. Booleans passed because Python subclasses `bool` from `int`, and
negative sample indices silently selected profiles through negative indexing.
Validation must happen before indexing or constructing RNG state.

**Rejected alternatives.** Coercion (`int(value)`), accepting booleans, clamping
negative indices, or validating only `generate` would preserve ambiguous API
behavior. Disallowing negative integer seeds was also rejected because seeds are
opaque deterministic keys and existing behavior was lawful.

**Evidence and failure modes.** The regression tests cover Boolean, float,
string, `None`, and negative-index cases for both entry points, plus deterministic
negative integer seeds. Invalid calls now fail explicitly; valid source-bound
sampling remains unchanged.

## D2 — Preserve canonical semantics and distribution

**Choice.** Make no change to the Racket authority, `RULE_HASH`, profile schedule,
geometry, axes, colors, semantic rivals, or lesson assembly. Advance only the
Python generator version from 3.0.0 to 3.0.1 for the API repair.

**Reason.** The baseline already passed 11 of 12 gates; distribution and semantic
checks were green. The defect was isolated to scalar validation, so changing the
puzzle manifold would add risk without addressing a measured failure.

**Evidence.** Final authority-set hash equals the baseline; the after battery is
12/12 green; profile floor is 60/60 exact and envelope support; the production
and fixed-schedule censuses remain unambiguous against the declared rivals.

## D3 — Keep `color_order` as a separate proposed parameter

**Choice.** Build a runnable task-local prototype with episode-level
`color_order` values `ascending` (canonical/default) and `descending`. Do not add
it to production `AXES`, generator sampling, canonical data, or approval hashes.

**Reason.** Reversing color precedence preserves the original object roles,
bounding-box operation, zero-only writes, and overlap reasoning while creating a
small genuine rule parameter. It is therefore suitable for authoring research,
but it changes semantics and needs separate approval.

**Construction.** The descending program changes exactly one canonical Racket
color-list expression. Four deterministic overlap fixtures are independent of
the hidden setting. Seed parity chooses one setting for a complete episode of
three demonstrations and one query. Public files omit the parameter, program,
seed, and query answer; private evidence retains them.

**Acceptance evidence.** Exact Racket execution reproduced all five canonical
labels under ascending order. Both settings were covered; each fixture separates
them; both production episodes and all eight query rotations refuted the rival.
The materialized tree self-verified seven manifest files.

**Limit.** This is proposed/unapproved and intentionally not part of the selected
canonical execution path.

## D4 — Make the prototype portable across staged task-test layouts

**Choice.** Load the selected generator from the explicit repository-layout mirror
beside the staged task and verify its SHA, rather than invoking the generic
selected-generator loader after `puzzle_generators` has already been imported
from the execution mirror.

**Reason.** The first portable snapshot passed 94 tests but failed four prototype
tests because the generic loader correctly rejected dependencies cached from a
different source tree. The task-test runtime deliberately contains both trees.

**Rejected alternative.** Clearing `sys.modules` or weakening the shared
cross-tree guard would hide a safety invariant. Direct source-mirror loading is
local, deterministic, and hash-checked.

**Evidence.** `checks/task-tests-final/result.json` retains the failure;
`checks/task-tests-final2/result.json` records 98/98 passing after the repair.

## D5 — Enumerate the declared lesson schedule in the final battery

**Choice.** Treat the ordinary after-battery command as an intermediate run and
rerun the final battery with `--enumerate-schedule-period --schedule-seed 0`.
Also retain a dedicated period census with query rotation.

**Reason.** The generator declares `LESSON_SCHEDULE_PERIOD = 5`. The ordinary
command completed all substantive sampling checks but correctly failed the
semantic gate with `declared_period_not_enumerated`. Explicit enumeration is
needed for a final aggregate pass.

**Limit.** Five residues across three bands at seed 0 exhaust the declared index
period at that seed only; they do not certify all seeds or undeclared rivals.

## D6 — Leave adversarial audit targets untouched

**Choice.** Reproduce and document findings for `f9dd4cf0f344` and
`2e4e1d2834ee` without modifying either source.

**Reason.** The audit contract is inspection-only. Repairs would exceed the
selected task scope and invalidate source binding.

**Evidence.** `AUDIT.md` names exact source hashes, reproducer paths, outcomes,
and owner-facing repair suggestions.

## D7 — Record the post-repair solve as exposed, not blind

**Choice.** Set `earlier-exposure=yes` and `reference-consulted=no`.

**Reason.** Generator work necessarily exposed the rule before the required
post-repair solve. During the solve itself, only visible examples and local
Python were used. The visible examples independently refute row-major precedence
and pass 3/3 under ascending-color zero-only rectangle filling.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/021fb6acf24f/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
