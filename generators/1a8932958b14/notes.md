# Current notes: 1a8932958b14

## Intended rule

A zero-background grid has exactly one red source marker (`2`), one green destination marker (`3`), and one nonempty 4-connected payload using colors other than `0/2/3`. Translate the whole payload by `green - red` onto a blank same-size grid, preserve every payload color, and drop the markers/original payload. Selected canonical `RULE_HASH`: `42869e666344`; the selected Racket authority was not changed in review `review-ed2ecc8c34b6218e`.

## Current generator assumptions

- Exact `int` seed; exact nonnegative `int` sample index. Booleans, floats, and strings fail closed.
- Difficulty is `None`, `easy`, `medium`, or `hard`.
- Grid dimensions `9..20`; payload size `3..9`; payload palette size `1..3`.
- All eight declared direction overrides are realizable, with nonzero vectors that keep the translated payload in bounds.
- Generated inputs pass `self_check` and `strict_canonical_like`; outputs come from the unchanged selected rule.
- A production lesson uses two demonstrations and one query.

## Reversed decisions and repairs

### Strict scalar boundary

Prior code validated difficulty/overrides but let `gen_ctx` accept invalid `seed` and `sample_index` scalars. The new call boundary validates them before context construction. Red evidence contained eleven accepted invalid values; final task tests and defect lint pass.

### Lesson schedule: 8 slots → 9 slots

Prior schedule: eight slots with canonical anchors at `0`, `3`, and `6`. This was safe for many linear windows but not cyclic query rotation: medium seed `20261008`, samples `6,7,8`, query `7` left monochrome up-right demos `6` and `8`. Both `canonical_up_right` and `translate_modal_payload_color` fit those demos and changed the query; the retained prior census found 36/900 ambiguous rotations.

New schedule: nine slots, anchors `0`, `3`, `6`, palette pattern `(1,2,2)` repeated, and directions:

`up_right, down_left, down_right, up_right, up_left, left, up_right, down_left, down`.

Every cyclic three-sample window now has at most one anchor. Holding out any sample leaves demos containing a multicolor witness and a case that semantically disagrees with the up-right shortcut. A first attempted `right` slot was rejected because its answer did not actually refute that rival; `down_left` replaced it.

### Portable tests

Prior focused tests depended on a legacy staged import and fixed-depth canonical path. They now use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

## Verification snapshot

Final generator SHA-256: `1754a515ea3eb89cf00bb871d647e249061a23305896dca3f4a2f6f456524a54`.

- Strict after battery: 12/12 green.
- Portable selected tests: 23/23 passed.
- Exhaustive declared schedule at seed `20261008`: 9 starts × 3 holdouts = 27/27 passed.
- Production lesson census: 300/300 identifiable, 0/300 ambiguous.
- Query rotations: 900/900 identifiable, 0/900 ambiguous; 900 unique inputs.
- Profile floor: 17/60 exact/envelope hits; support in every band.
- Authority set unchanged; selected execution parity passes.

Counterexamples and focused evidence for this review are under `counterexamples/review-ed2ecc8c34b6218e/` and `WORK/checks/` in the return.

## Proposed parameter variant (not production-approved)

`workspace/parametric/` contains a runnable episode-level `vector_multiplier ∈ {1,2}` prototype. Default `1` preserves canonical behavior; `2` moves by twice the red-to-green vector. One setting is fixed across three demonstrations and one query, all shifted cells must remain in bounds, and public exports hide the parameter/program/query outputs. Both exact Racket programs were executed and each episode’s demos refute the opposite setting. This does not change the production generator, canonical rule, or approval state.

## Known limits and open findings

- Rival checks are finite; zero ambiguity against declared/searched competitors is not universal proof of unique induction.
- The 300-lesson census samples deterministic seeds and reports sampler period six; it does not enumerate the explicit nine-slot task schedule. The separate 27-case probe covers every declared start at one seed.
- The deterministic teaching schedule may leak slot-order correlations if consumers expose global indices; vary starts and keep running rotation/rival checks.
- The parametric prototype has bounded two-setting evidence only and needs a shared production API/approval decision before use.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-b74b5b5c70306a18:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `60833338187fe73b858c1c2bb7ff6e118e0023b2092a55492116bfb5dd6c3717`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused repair-bound closure against1754a515ea3eb89cf00bb871d647e249061a23305896dca3f4a2f6f456524a54 ofold60833338187fe73b858c1c2bb7ff6e118e0023b2092a55492116bfb5dd6c3717 rotation/portable-test/scalar findings. Owner staticinspection confirms _validate_call checksactualseed/index beforegen_ctx,ninepalette/direction slots withanchor0/3/6,andtest_every_three_sample_schedule_window_survives_every_query_rotation coversseed20261008allnine starts/threeholdouts. Reviewerfocused23tests/full77252-filepatchreplay+fresh23tests,checks/schedule-exhaustive.json27/27 and300lessons/900rotations directlyexercisepriorbad6/7/8window andrivals,notgenericacceptanceclosure. Portablehelperimportsnowfind_root/canonical_path/canonical_pairs;earlierfailed8-slot/intermediate18/19evidence retained. Finite declaredrivals/seeds,notowner batteryexecution.

### Assessment or prior finding

## 1a8932958b14

### A2 — Reproduced arbitrary-query lesson ambiguity

Audited generator SHA-256:
`60833338187fe73b858c1c2bb7ff6e118e0023b2092a55492116bfb5dd6c3717`.
Canonical rule hash: `42869e666344`.

I reproduced the unresolved source-hash-matched counterexample with fresh Racket
labels. At medium seed `20261008`, samples `6`, `7`, and `8`, holding sample `7`
out as the query leaves samples `6` and `8` as demonstrations. Both demos are
monochrome up-right translations; the query is a multicolor downward
translation. The declared `canonical_up_right` and
`translate_modal_payload_color` rivals both match every demo and both disagree
with the authoritative query output. All three inputs pass `self_check`, and all
three Python mirror outputs match the fresh Racket receipt.

Evidence:

- `checks/audit/1a8932958b14/input.json`
- `checks/audit/1a8932958b14/racket-fresh.json`
- `checks/audit/1a8932958b14/fresh_rotation_summary.json`
- `checks/audit/1a8932958b14/reproduce_rotation.py`
- `checks/audit/1a8932958b14/reproduce_rotation.log`

The fresh peer-audit preset separately reproduces the portable task-test defect:
preflight exits before pytest because the test imports the legacy staged
namespace and uses a fixed-depth canonical-data path. The semantic smoke itself
passes in production order, so it does not resolve A2. Evidence:
`checks/audit/1a8932958b14-combined/result.json` and
`checks/audit/1a8932958b14-combined-driver.log`.

No audit-only source was modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-b74b5b5c70306a18-v0001/audit_assets.json), manifest SHA-256 `bc8196d17fc2cd3262d28806a58af9f69cf5611d56dac48d488a8a2dd734c417`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `1754a515ea3eb89cf00bb871d647e249061a23305896dca3f4a2f6f456524a54`.

# Decisions: 1a8932958b14

## D1 — Keep the selected Racket authority unchanged

**Prior choice.** The selected canonical rule already expressed color-preserving translation by the red-to-green vector. Historical source roles intentionally keep an archival spelling separate from the selected synchronized spelling.

**Decision.** Change only generator validation, teaching schedule, tests, notes, counterexamples, and task-local prototype files. Keep `RULE_HASH=42869e666344`, the canonical row, and selected Racket program unchanged.

**Alternatives rejected.** Rewriting the Racket rule or refreshing authority hashes would not address either observed defect and could erase the explicit archival/selected distinction.

**Probe/evidence.** `checks/after/checks/1a8932958b14_after_authority_sync.json` reports selected synchronization and execution parity. The before and after battery summaries carry the same authority-set SHA-256.

**Failure mode/limit.** Authority parity establishes label continuity, not lesson identifiability; that is checked separately.

## D2 — Reject coercible call scalars before context construction

**Prior choice.** `_validate_call` validated difficulty and override types but did not receive `seed` or `sample_index`. `gen_ctx` therefore accepted values such as booleans, integer-valued floats, strings, and negative indices.

**Decision.** Require `type(seed) is int`; require `type(sample_index) is int and sample_index >= 0`. Perform this before creating `gen_ctx`.

**Alternatives rejected.** `isinstance(value, int)` would still admit booleans. `int(value) == value` would admit `1.0` and coercible strings. Validation after context construction would permit normalization or state derivation from invalid values before failure.

**Probe/evidence.** Eleven parametrized red tests in `checks/task-tests-red/result.json`; retained values in `counterexamples/review-ed2ecc8c34b6218e/strict_scalar_cases.json`; final defect lint green.

**Failure mode/limit.** The public API now intentionally rejects callers that relied on coercion. This is a contract correction, not backward compatibility.

## D3 — Replace the 8-slot lesson cycle with a 9-slot cycle

**Prior choice.** The previous cycle had anchors at `0`, `3`, and `6` but length eight. That spacing looked regular in linear windows, yet cyclic window `6,7,0` contained two anchors.

**Decision.** Use a nine-slot cycle with anchors `0`, `3`, and `6`; palette pattern `1,2,2` repeated three times. Every cyclic three-sample window then has exactly one monochrome anchor and two multicolor cases.

**Alternatives rejected.** Moving one anchor inside the eight-slot cycle merely relocates a wraparound collision. Removing an anchor reduces canonical-profile support. Raising the demonstration floor would change the intended two-demo curriculum and cost more tokens.

**Probe/evidence.** Baseline reproduction `rotation_baseline.json`; exhaustive final receipt `checks/schedule-exhaustive.json`; broader census `checks/lesson-census.summary.json`.

**Failure mode/limit.** A deterministic schedule can itself become a learnable correlation if consumers preserve global slot order. Consumers should vary lesson starts and not expose slot metadata.

## D4 — Define orientation witness by rival disagreement, not token name

**Prior choice.** “Noncanonical direction” was intended to refute the public-only `canonical_up_right` shortcut. A candidate rightward slot appeared non-up-right by name.

**Decision.** A valid witness must make `_canonical_up_right(input) != rule_mirror(input)`. The final slot uses `down_left`, which actually distinguishes the outputs.

**Alternative rejected.** Keeping `right` would satisfy a syntactic direction check but not the semantic teaching requirement. The first green attempt demonstrated this with one remaining failed rotation.

**Probe/evidence.** `checks/task-tests-green-1/result.json` (`18 passed, 1 failed`) and `checks/task-tests-green-2/result.json` (`19/19`).

**Failure mode/limit.** The predicate is specific to one declared rival. Other plausible direction shortcuts still require their own competitors or probes.

## D5 — Preserve the full exact-override domain

**Decision.** Keep all eight direction tokens and every declared grid/payload/palette boundary realizable through exact overrides, even though the default nine-slot schedule does not include every token.

**Rationale.** The default schedule is pedagogical; exact controls are authoring and coverage interfaces. Shrinking the declared domain would trade a curriculum repair for a distribution regression.

**Probe/evidence.** Focused override tests across all bands and directions; after override stage green; `checks/after/checks/1a8932958b14_after_override_results.json`.

**Failure mode/limit.** Passing exact controls does not imply balanced default frequencies.

## D6 — Make selected tests portable rather than weakening the task-test gate

**Prior choice.** The test imported `scripts.canonical_profile_gate` and inferred canonical paths from fixed parent depth. This worked only in one layout.

**Decision.** Use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`; compute the short rule hash locally from the canonical row.

**Alternatives rejected.** Skipping the inherited file or treating no portable execution as a pass would hide regressions. Modifying shared runtime code is outside the selected task patch.

**Probe/evidence.** `checks/task-tests-before/result.json` versus final `checks/task-tests/result.json` (23/23).

**Failure mode/limit.** One base-solution path remains intentionally checked because this task’s selected/archival role metadata is itself part of the regression contract.

## D7 — Add a vector-multiplier prototype, but do not promote it

**Parameter.** `vector_multiplier ∈ {1,2}`; default `1`.

**Decision.** Keep a task-local episode generator and evidence builder under `workspace/parametric/`. Select one value per deterministic episode; use it for all demonstrations and query; require all shifted cells to stay in bounds.

**Alternatives rejected.** Varying only grid size, position, palette, or direction would change inputs without changing the executed rule. A per-pair multiplier would make a single lesson internally inconsistent. Editing the selected generator or canonical authority would falsely imply production support.

**Probe/evidence.** `checks/parametric/summary.json`, complete episodes, masked challenges, and exact Racket programs in `checks/parametric/`.

**Failure mode/limit.** Only two settings and one seed per setting were executed. Shared production integration, sampler policy, and approval are unresolved.

## D8 — Treat query rotation as required for this repaired curriculum

**Decision.** Test every pair as query because the downstream review contract explicitly permits arbitrary holdout diagnostics and the defect was caused by query position. The generator’s small schedule makes exhaustive local testing cheap.

**Alternative rejected.** Declaring a fixed-last-query curriculum would preserve the baseline ambiguity and make data quality depend on an undocumented assembly invariant.

**Probe/evidence.** 27 exhaustive schedule holdouts and 900 broader materialized rotations.

**Failure mode/limit.** Rotation of already materialized pairs does not sample new inputs. The random census and exhaustive schedule probe are complementary, not interchangeable.

## D9 — Leave peer-audit targets unchanged

**Decision.** Reproduce source-bound defects for `generic_gather_gen3` and `6d26bc40cbb2`, retain exact probes, and make no audit-only source edits.

**Rationale.** The assignment asks for adversarial review, not repair, and the package patch scope belongs to `1a8932958b14`.

**Probe/evidence.** `AUDIT.md` and `checks/audit/`.

## D10 — Report the production-census period discrepancy instead of overclaiming

**Observation.** The production census companion reports sampler `period: 6`, while the repaired generator declares nine schedule profiles. The census documentation also states that it does not enumerate every possible schedule start.

**Decision.** Use the census only for its actual 300 sampled lessons and 900 rotations, and add a separate source-bound nine-start exhaustive probe. Do not describe the random census as schedule-exhaustive.

**Failure mode/limit.** The inferred period may reflect shared runner metadata rather than the task’s explicit schedule. Shared tooling should prefer a declared schedule period; see F1/F2 discussion in `FEEDBACK_TO_CODEX.md`.

## Native parametric promotion candidate: payload-axis gate

The prior `vector_multiplier` draft was useful authoring evidence but did not
meet the current MAIN contract: it lacked a native adapter/promotion contract,
four-query and 30×30 support, and a non-cosmetic input-dependent Step-A → Step-B
dependency. The current candidate therefore leaves the production generator and
selected canonical authority unchanged while adding a separate native family.

### D11 — Use payload axis as the alternative rule's causal intermediate

**Parameter.** `translation_policy ∈ {marker_vector, payload_axis_gate}` with
canonical default `marker_vector`.

**Step A.** Compute the non-marker payload's bounding box and classify it as
`wide` or `tall`.

**Intermediate.** `payload_axis`.

**Step B.** Translate the payload using the red-to-green marker vector with
multiplier `+2` for `wide`, or `-1` for `tall`. The canonical setting always uses
multiplier `+1`.

**Why this design.** It preserves the original marker-vector and payload-motion
reasoning while requiring an input-derived branch before the final transform can
be selected. It is stronger than the historical fixed multiplier draft and does
not collapse to a cosmetic remap or fixed post-processing step.

**Input grammar.** Every generated scene keeps the `-1`, `+1`, and `+2`
translations in bounds. Payloads are dense, multicolor, 4-connected,
non-square-bounding-box objects. The minimum two-demo lesson presents a matched
wide/tall pair; query profiles include 26×30 and substantive 30×30 boundary cases.

**Causal witness.** `WORK/checks/1a8932958b14/native-evidence/causal/witness.json`
is generated by the repository's official witness builder from the exact native
qualification receipt. It executes the selected alternative and a protected-Racket
rule that forces the wrong `tall` intermediate on a wide payload. The correct `+2`
and wrong `-1` translations produce different final grids; both the generated
replay and an independent `review_witness check` report `reviewer_replayed`.

### D12 — Keep the exact canonical program as a source-hash-checked resource

`workspace/parametric/canonical.rkt` is the selected catalog program byte-for-byte
(SHA-256 `aa6d40d026b329b0b5f7a9aa1e89644629386b057e095d94ab2e5e33db2d9777`).
The adapter rejects source drift before returning it. No production generator,
canonical rule row, or `RULE_HASH` changed.

### D13 — Make two demonstrations sufficient without correlated shortcuts

The first two demonstrations share a 14×14 field, the same marker vector,
palette cardinality, and dense irregular construction. Their payload boxes are
transposes: first wide, then tall. This refutes the other declared setting and
fixed-double/fixed-reverse, swapped-axis, vector-orientation, and palette-parity
shortcuts without increasing the minimum demonstration count.

The finite self-review covers seeds 0 and 17, both settings, minimum two-demo
lessons, four queries, three protected-Racket rivals, and five additional Python
rivals. No tested harmful survivor remained. This is finite evidence, not a proof
of unique induction.

### D14 — Support stable independent counts and realistic large queries

Demo and query streams use separate stable seed namespaces. Prefixes are unchanged
when either count grows: 2–6 demos and 1–4 queries are supported, and the first
query is identical between single-query and four-query use. The four query sizes
are 18×22, 22×18, 26×30, and 30×30. The 30×30 payload has at least 140 cells,
multiple colors, interior holes, and a legal boundary contact.

### Verification snapshot for native candidate

- Focused native adapter tests: 47 passed.
- Full staged changed-target task suite: 70 passed.
- Protected-Racket native qualification: qualified, two settings × seeds 0 and
  17, three demos and four queries, 40 Racket evaluations.
- Minimum-lesson native evidence: four jobs, all stored labels replayed through
  protected Racket; no tested harmful survivor.
- Public saved-file check: two files, four masked queries each, no findings.
- Deterministic seed sweep: 256 seeds, 512 episodes, 5,120 pairs, zero failures;
  this sweep is Python/self-check evidence and does not replace qualification.

Owner exact-source acceptance remains pending. Training admission remains false.
