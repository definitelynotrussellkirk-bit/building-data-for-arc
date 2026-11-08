# Working notes: 084de7b050a1

## Current selected source

- Generator SHA-256: `e9e4cab81b481534073f9f04311f84c83e1ccae8cef1e7080a5ba4caa16fcc26`
- Canonical rule hash: `e059ff61aa1e`
- Version: `3.0.0` (intentionally unchanged; lawful draw semantics are unchanged)

## Intended rule

Color `1` is the original source set. Singleton colored dots act in row-major
order. A dot uses the first blue cell in the same column when available,
otherwise the first blue cell in the same row. The entire original blue set is
reflected across the midpoint of the dot and anchor, clipped cell-by-cell, and
painted in the dot color. Unaligned dots are inert and later dots win overlap.

The production curriculum is an ordered five-profile cycle:
`core_connected`, `global_disconnected`, `priority_first_match`, `inert_decoy`,
and `clip_overlap`. Every complete production window is intended to expose the
branch, global-set, anchor-priority, inertness, clipping, and overwrite details.

## Review-7e5adee586952042 decisions

1. Added exact scalar validation before context construction. `seed` and
   `sample_index` must be exact integers, sample index must be nonnegative,
   `difficulty` must be `None|easy|medium|hard`, unknown axes fail, and declared
   integer axes use `draw_int_strict`.
2. Kept version and valid draws unchanged. A 528-call before/after fingerprint
   has identical records hash
   `2e48ea06c2bdeb9641e956d82af68d46c50dca6ed6f1064c47c9d07fa186e65d`.
3. Repaired selected task-test portability with `reviewer_support`; selected
   Racket sources are bound by normalized hash rather than whitespace-sensitive
   raw equality. Final isolated suite: 29 passed.
4. Kept shared authority untouched. The after battery found formatting-only
   selected-source drift; `checks/authority-sync-proposal.json` is non-applying
   because this assignment forbids shared-authority writes.
5. Added a proposed task-local `axis_priority` prototype under
   `workspace/parametric/`. Canonical `column_first` remains production;
   `row_first` is not selected or approved.

## Evidence and limits

- Full after battery: 11 green stages; only exact-text authority synchronization
  fails. Rule smoke, semantic gate, override checks, and Racket lint pass.
- Large census: 300/300 production lessons identifiable over 1,800 pairs and
  1,732 unique inputs. Arbitrary rotations are not promised and 752/1,800 are
  ambiguous when a decisive profile is held out.
- Prior source-bound audit findings about scalar permissiveness and nonportable
  tests are repaired by this source. The earlier `31/72` rotation finding remains
  a documented domain limitation, expanded here to `752/1,800`.
- Finite declared-rival checks do not prove uniqueness against every possible
  hypothesis. Downstream assemblers must preserve the ordered teaching window or
  rerun distinguishability checks after shuffling.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ed3fa9eab5868499:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7de0e73a7b4472fadc6e5185f3f51aca947f028ef8ecc62c29eb3ab7a8dc086d`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

The earlier audited baseline SHA 7de0e73a7b4472fadc6e5185f3f51aca947f028ef8ecc62c29eb3ab7a8dc086d had a bounded no-issue report: ten canonical pairs, 600 ordered lessons and six Racket parity spot checks. Explicitly triage that original report as no_issue within its scope; it does not close later scalar, portability, authority-sync or arbitrary-rotation findings, and is not a new execution on repaired bytes.

### Assessment or prior finding

## 084de7b050a1

**No issue found in the checked scope.**

Generator SHA-256:
`7de0e73a7b4472fadc6e5185f3f51aca947f028ef8ecc62c29eb3ab7a8dc086d`.
Declared and executed Racket rule hash: `e059ff61aa1e`.

I checked all 10 canonical pairs against the target's five declared canonical
shortcuts; every declared shortcut genuinely fits every canonical pair. I then
probed easy, medium, and hard bands, seeds `0..19`, and cyclic starts `0..9`,
using five consecutive demonstrations followed by the next query. That is 600
lessons over 900 generated pairs and 773 unique inputs. The target's
`lesson_identifiable` hook reported zero failures. As an independent parity spot
check, six generated medium examples at seed 7/sample indices `0..5` matched the
selected Racket outputs exactly.

The compact evidence and full scope are in
[`checks/audit/084de7b050a1/window_probe.json`](checks/audit/084de7b050a1/window_probe.json),
with Racket receipts in
[`checks/audit/084de7b050a1/racket.json`](checks/audit/084de7b050a1/racket.json).
This is finite evidence against the declared rivals and sampled schedules; it is
not a proof against undeclared rules or every possible seed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ed3fa9eab5868499-v0001/audit_assets.json), manifest SHA-256 `777a1e993d4b8d3620917b78b0f3e43c2fcbdf860dab6ea623a28f9b72dc7c43`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `e9e4cab81b481534073f9f04311f84c83e1ccae8cef1e7080a5ba4caa16fcc26`.

# Decisions: 084de7b050a1

## D1 — preserve the five-profile valid distribution

**Prior choice.** The generator used a deterministic five-profile schedule:
`core_connected`, `global_disconnected`, `priority_first_match`, `inert_decoy`,
and `clip_overlap`.

**Decision.** Preserve every lawful generated grid and keep `VERSION = "3.0.0"`.

**Rationale and alternatives.** The schedule already teaches all 11 declared
semantic witnesses in production order. Rebalancing profiles or incrementing the
version would create needless data drift. A 528-call fingerprint proves the
repair changes no lawful inputs or Python-mirror labels. The alternative—changing
sampling while fixing validation—would confound the defect repair with a new
curriculum experiment.

**Limits.** The fingerprint is finite and source-bound; Racket parity is covered
separately by rule smoke and the semantic gate.

## D2 — reject malformed controls before constructing the draw context

**Prior choice.** The baseline delegated permissive values to generic context and
integer helpers, allowing bools, numeric strings, floats, and negative sample
indices to produce lawful-looking examples.

**Decision.** Validate exact types/ranges at the top of `generate` and use
`draw_int_strict` for every declared integer override.

**Alternatives rejected.** Silent coercion hides caller errors and can collapse
distinct experiment configurations onto the same draw. Validating only inside
individual profile builders would duplicate policy and leave `seed`,
`sample_index`, and `difficulty` exposed. The selected centralized guard is
small, deterministic, and covered by a 21-case parameterized test.

**Failure mode retained.** Values outside an axis's finite range still raise from
the strict draw helper; unknown axes raise before generation.

## D3 — make task tests portable and bind semantics by normalized rule hash

**Prior choice.** Tests inferred repository root from a fixed parent depth,
imported a legacy `scripts` helper, and required raw Racket text equality.

**Decision.** Use the public `reviewer_support` API and compare selected sources
by the same whitespace-normalized 12-character rule hash used by the generator.

**Alternatives rejected.** Copying shared data into the selected task would create
a stale duplicate. Keeping raw byte equality in the task test would reject
formatting-only differences while still not replacing the dedicated authority
synchronization gate.

**Limit.** Normalized hashing proves token identity only within this restricted
source form; execution parity remains the responsibility of Racket smoke and
canonical-pair checks.

## D4 — do not apply the shared authority proposal

**Observation.** The after battery found two selected `target_code` strings that
are token-equivalent to canonical `program_solution` but not exact-text equal.

**Decision.** Retain a non-applying proposal in
`checks/authority-sync-proposal.json` and leave both shared files untouched.

**Rationale.** Assignment metadata says `shared_authority_write_allowed=false`
and `requires_racket_patch=false`. Applying a formatting-only shared-data patch
would violate the selected-task edit boundary. The maintainer has all source
hashes, changed JSON pointers, and verification commands needed for a separate
explicit action.

## D5 — retain ordered curriculum; report rotations as diagnostic

**Decision.** Do not change the five-profile schedule to make every arbitrary
query rotation identifiable.

**Evidence.** The 300-lesson census found 0/300 ambiguous production lessons but
752/1,800 ambiguous rotations. The missing witness is concrete: holding out the
`priority_first_match` profile can leave `row_priority_when_both_aligned`
unrefuted.

**Rationale.** Production intentionally emits a complete five-profile teaching
window before the query. Enforcing all rotations would optimize for a downstream
assembly policy the generator does not declare, and could unnecessarily inflate
or duplicate demonstrations.

**Limit.** Downstream systems must preserve production ordering or independently
revalidate any shuffled/rotated lesson.

## D6 — prototype `axis_priority` separately

**Decision.** Provide `column_first|row_first` as a task-local proposed prototype,
selected once per episode, while leaving canonical production fixed at
`column_first`.

**Why this parameter.** It changes an actual executed branch without changing the
family's core reflection reasoning. A both-aligned marker is a decisive witness,
and the prototype includes it in demonstration index 2 before a differing query.

**Alternatives rejected.** Grid size, color, profile frequency, and object
position are input parameters rather than rule parameters. Per-pair resampling of
priority would make the lesson incoherent.

**Limits.** The prototype demonstrates two bounded settings and exact Racket
execution for one source-bound episode each; it is not a production API or an
approval claim.

## D7 — current ARC design characterization

- `contextual_gating`: present. Marker alignment selects the column or row branch;
  the both-aligned profile distinguishes column priority from a row-priority rival.
- `sequential_state`: present. Markers act in row-major order and later reflected
  paint overwrites earlier paint; `earlier_dot_wins_overlap` is the rival.
- `multi_rule_interaction`: present. Anchor selection, whole-set reflection,
  cellwise clipping, and overwrite order jointly affect outputs.
- `task_defined_symbols`: not applicable in the selected generator because the
  roles of background `0`, source blue `1`, and singleton marker colors are fixed.

These are reviewer-reported, source-bound observations, not corpus-wide coverage
claims.

## Self-review

The repair does not change valid draws, the canonical rule, or shared authority.
Every new behavior has a failing-before/passing-after test. The exact final
source patch also applied cleanly to a fresh extraction of the original packet;
all nine changed paths hash-matched and the replayed isolated suite passed 29/29.
The only full-battery failure is recorded rather than suppressed. Audit-only
targets remain unedited, and the proposed parametric variant is physically and
semantically separated from selected production.
