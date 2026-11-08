# Current notes: 9bd5d9c04dd8

## Selected implementation

Version `3.0.2`; generator SHA-256
`856492829e5c36878805064f6a9fda3846e0980700349b7d5556a9d10ad21e8a`.
The selected canonical Racket rule is unchanged and remains pinned by
`RULE_HASH = b484d9374fb6` (full SHA-256
`b484d9374fb696d5e51530eed27785c822c8973c5a4f9be6d521546e72200a12`).

The authority scans candidate top-left positions in row-major order. A candidate
is a fully nonzero 3×3 tile whose four orthogonal border strips are background
(or outside the canvas). It returns the candidate with the greatest number of
color-1 cells; strict comparison makes the first row-major candidate win a tie.
Generated lessons use two to four candidates with distinct color-1 counts, one
shared nonzero fill color, no stray nonzero cells, and a unique winner after the
first row-major tile.

The selected distribution retains the prior repaired design:

- exact controls are `grid_h=8..16`, `grid_w=9..18`, `tile_count=2..4`, and
  `fill_color=2..9`;
- even sample indexes use the canonical 9×9 profile while odd indexes explore
  the declared shape ranges;
- default fill colors avoid canonical color 8 so lessons refute the declared
  “most non-8” shortcut, while exact `fill_color=8` remains legal;
- easy/medium/hard default to two/three/four candidate tiles, but exact tile
  counts remain available in every band;
- generated counts are distinct, so tie behavior is authority-tested rather
  than taught by the production sampler.

## Review repair: strict public call contract

The pinned `3.0.1` source accepted malformed top-level request controls. The
before defect linter recorded 45 warnings: booleans, floats, strings, and/or
negative values were accepted for `seed`, `sample_index`, or `difficulty`.

Version `3.0.2` adds `_validate_call` before generator context construction:

- `seed` and `sample_index` must be exact nonnegative Python integers, not bools;
- `difficulty` must be `None`, `easy`, `medium`, or `hard`;
- malformed requests now fail with `ValueError` before sampling state exists.

The repair does not alter the canonical rule or lawful support. The version bump
intentionally rekeys deterministic valid samples, while preserving the same
construction algorithm and advertised domains. Focused call-contract tests first
failed 17 cases and then passed 21/21 after the validator was added.

## Proposed parametric extension (not canonical)

`workspace/parametric/prototype.py` implements one hidden episode-level
parameter:

| Parameter | Values | Canonical default |
| --- | --- | --- |
| `selection_mode` | `most`, `fewest` color-1 cells | `most` |

`most` materializes the exact selected canonical Racket program. `fewest`
changes only the extremum initialization and strict comparison, preserving
candidate geometry, color-1 counting, crop behavior, and row-major tie policy.
The parameter is selected once for a complete three-demonstration/one-query
episode. Public artifacts omit the hidden setting, Racket text, and query label.

Retained seeds `0,1,2,4` cover both settings (`most,most,most,fewest`). Both exact
Racket programs agree with an independent Python mirror, and every demonstration
and query differs under the rival setting. Evidence is under
`checks/parametric/selection-mode-v1/`; the program hashes are:

- `most`: `b484d9374fb696d5e51530eed27785c822c8973c5a4f9be6d521546e72200a12`;
- `fewest`: `54fded751f9ae4857e277ab260577fc8eeafba135f5543210c6959c16751b705`.

This is a proposed authoring extension only. It does not change the production
generator, canonical authority, approval state, or training admission.

## Final evidence

- `checks/after/checks/9bd5d9c04dd8_after_battery_summary.json`: all 12 strict
  after stages green, no advisories or incomplete stages.
- `checks/task-tests/result.json`: portable selected-task snapshot, 81/81 tests
  passed.
- `checks/after/checks/9bd5d9c04dd8_after_profile_floor.json`: 38/60 exact
  canonical-profile hits (easy 14/20, medium 11/20, hard 13/20).
- `checks/after/checks/9bd5d9c04dd8_after_override_results.json`: 32,040 exact
  override draws, no findings, unknown key rejected.
- `checks/lesson-census-review.summary.json`: 300 lessons, 1,200 pairs and 1,200
  required query rotations; zero ambiguity, hook warnings, scoring errors, or
  materialization errors against the declared rival.
- `solve/summary.json`: fresh exposed solve bound to the final generator bytes;
  revision 1 passed all three visible examples, with earlier rule exposure
  declared `yes` and reference consultation `no`.

## Known limits

The lesson evidence is finite and covers the declared “most non-8” rival, not all
possible programs. Explicit all-color-8 lessons can recreate that canonical-fit
ambiguity and should not be assembled alone. The production sampler does not
teach tie behavior. The proposed `fewest` setting is verified only on retained
generated episodes and remains separate from the selected canonical path.
Catalog approval and training admission remain maintainer decisions.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-27ad3777a90f6d7f:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a9d5e86f13a11ac06fdde3267d72af6f16560812ae8ecc8fe0e12205f66d51aa`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved on accepted source 856492829e5c36878805064f6a9fda3846e0980700349b7d5556a9d10ad21e8a by exact integer/nonnegative call validation before generator state construction. The older audited source a9d5e86f13a11ac06fdde3267d72af6f16560812ae8ecc8fe0e12205f66d51aa accepted boolean, float and negative sample indices; generators/9bd5d9c04dd8/tests/test_call_contract.py and the returned 81-test portable receipt cover those cases, and the final strict battery reports zero findings. This is reviewer-reported repair evidence from review-5f48281bad7cf2b0:v0001, not an owner rerun or resolution of other audits.

### Assessment or prior finding

## 9bd5d9c04dd8

**Reproduced request-contract defect:** the selected generator accepts invalid
`sample_index` scalars. With source SHA-256
`a9d5e86f13a11ac06fdde3267d72af6f16560812ae8ecc8fe0e12205f66d51aa`,
`generate(seed=731, difficulty="easy", sample_index=value)` accepted `True`,
`False`, `1.0`, and `-1`. Every returned grid passed `self_check` and its axes
were observable, so this is not a bad-label finding; it is silent acceptance of
requests outside the normal nonnegative-integer index contract.

The current shared `defect_lint` independently reproduced the same four cases
and failed with four `strict-scalar` warnings. The target's 51 portable task
tests all passed, showing that this edge contract is not covered there. Exact
values, output hashes, and observed axes are in
`checks/audit/9bd5d9c04dd8/summary.json`; the linter receipt and log are under
`checks/audit/9bd5d9c04dd8-defect-lint/`, and the passing task-test receipt is
under `checks/audit/9bd5d9c04dd8-task-tests/`.

No target source was modified. A bounded repair would validate `seed` and
`sample_index` before using parity/sampling logic, with a focused RED/GREEN test.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-27ad3777a90f6d7f-v0001/audit_assets.json), manifest SHA-256 `49b18daeb6ae1d387bc844f53e79b5c120a64d7307731a3358e01a5e245cebed`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `856492829e5c36878805064f6a9fda3846e0980700349b7d5556a9d10ad21e8a`.

# Decisions — review-5f48281bad7cf2b0

## D1 — Reject malformed top-level request controls before `gen_ctx`

**Prior choice.** Version `3.0.1` relied on downstream context behavior and did
not validate `seed`, `sample_index`, or `difficulty` itself. The strict before
probe accepted booleans, floats, strings, negative sample indexes, and unknown
difficulty values, producing 45 warnings.

**Decision.** Add one `_validate_call` at the start of `generate`: exact
nonnegative Python integers for `seed` and `sample_index`, and only `None`,
`easy`, `medium`, or `hard` for `difficulty`.

**Why.** These values identify and stratify training examples. Silent coercion
can alias requests, defeat replay, and mix difficulty bands. Rejecting before
state construction gives one deterministic failure boundary and matches the
already-strict exact override contract.

**Rejected alternative.** Coercing numeric strings/floats or merely warning
would preserve ambiguous aliases. Patching `gen_ctx` globally was out of scope
and could alter unrelated generators.

**Probe and limit.** A test-first regression failed 17 malformed cases, then
passed 21/21 after the change. The final defect lint is clean. Exact third-party
integer scalar classes are not accepted; the public contract is deliberately
plain Python `int`.

## D2 — Preserve the selected rule and lawful distribution

**Decision.** Do not change `RULE_HASH`, canonical Racket text, candidate
geometry, winner criterion, declared axes, or production lesson schedule.
Increment the implementation version to `3.0.2` because the callable API changed.

**Why.** The reproduced defect was request validation, not rule semantics or
input support. The existing selected distribution already passes strict
profile, override, semantic, diversity, and authority checks.

**Consequence.** Because version participates in deterministic RNG seeding,
valid examples are rekeyed even though the construction algorithm and support
are unchanged. All final checks and the exposed solve are bound to the new
source hash.

## D3 — Parameterize the comparison direction, not object geometry

**Requirement.** Assess one or two small episode-level parameters while
preserving the original reasoning pattern and canonical default.

**Decision.** Prototype one hidden `selection_mode ∈ {most, fewest}`. Keep
`most` as the exact canonical default. Materialize `fewest` by changing only
`best-n=-1`/`>` to `best-n=10`/`<` in the exact Racket program.

**Why.** This is the smallest meaningful rule variation: both settings require
finding the same isolated 3×3 objects, counting color 1, comparing candidates,
and returning an unchanged crop. Varying tile dimensions, isolation geometry,
or target color would change the task’s object roles more substantially.

**Rejected alternatives.** A tie-direction parameter would not be teachable
under the production sampler’s deliberately distinct counts. A target-color
parameter would confound comparison direction with palette semantics and would
require a new input distribution.

**Evidence.** Retained seeds `0,1,2,4` cover both settings. Four complete
three-demo/one-query episodes pass exact Racket/Python parity; every demo and
query distinguishes the selected setting from its rival. Program hashes and
public/private evidence are under `checks/parametric/selection-mode-v1/`.

**Status and limit.** Proposed only. It does not change production selection,
canonical authority, approval, or training admission. Evidence is bounded to
retained generated episodes; tie behavior remains outside the prototype’s
teaching support.

## D4 — Require both production-order and query-rotation lesson evidence

**Decision.** Retain the ordinary three-demo/one-query policy and run the larger
census with `--rotate-query` under a required rotation policy.

**Why.** The declared `most_non_eight` rival fits all ten canonical pairs, so
correct individual labels are insufficient. The lesson demonstrations must
refute it regardless of which generated pair is held out.

**Evidence.** 300 production lessons and 1,200 rotations have zero ambiguity,
materialization errors, scoring errors, or hook warnings. This remains a finite
rival test and is not described as universal identifiability.

## D5 — Keep audit findings separate from the selected repair

**Decision.** Do not edit `a5b0638997f5` or `f3672f3f540b`. Preserve source-bound
reproducers and failed strict audit receipts under `checks/audit/`, and report
them in `AUDIT.md`.

**Why.** The assignment permits only the selected task delta. Mixing peer fixes
would make the return unsafe to replay and obscure which checks apply to which
source hash.

## D6 — Promote `selection_mode` to the native finite adapter contract

**Decision.** Retain `selection_mode ∈ {most, fewest}` with exact canonical
`most` bytes, but replace the fixed three-demo/one-query prototype boundary with
native `program(settings)` and `generate(seed, settings, demos, queries)` entry
points. The supported contract is 2–6 demonstrations and 1–4 queries; native
qualification uses three demonstrations and all four queries.

**Construction.** Inputs are sampled from split/index-specific deterministic
streams that do not depend on the hidden setting. Every scene contains isolated
3×3 candidates with distinct color-1 counts, so all visible demonstrations
separate the two programs. Demo count does not shift query inputs, query count
does not shift demonstrations, and all inputs in an episode are distinct. The
fourth query is a substantive 30×30 scene with at least eight candidates and
non-candidate distractors.

**Evidence.** The focused file has 16 passing tests; the complete task suite has
88 passing tests. Native qualification covers settings `most` and `fewest` on
seeds 0 and 17 with three demonstrations, four queries, and 40 protected-Racket
evaluations. Public projection produces 16 independently verified single-query
views; first-turn checking covers four episode starts and 24 private-field
invariance mutations. Exact receipts are under `checks/9bd5d9c04dd8/` and
`checks/9bd5d9c04dd8-tests/`.

## D7 — Preserve real score-to-crop dependence and reject fixed-candidate bypasses

**Sequential dependency.** Step A enumerates isolated tiles, counts color-1
cells, and selects the setting-specific extremum. Its intermediate is the
input-dependent top-left coordinate. Step B crops the tile at that coordinate.
A protected-Racket `skip_a` witness substitutes the first candidate and changes
the final tile. The bounded self-review rejects the first-candidate shortcut on
64 setting/pair checks and verifies 64 protected-Racket labels across count
boundaries.

**Status and limit.** The source inventory, native qualification, sibling
execution evidence, public projection, and causal witness are ready for owner
acceptance. This is finite evidence, not universal rule uniqueness, measured
training benefit, owner acceptance, or training admission.
