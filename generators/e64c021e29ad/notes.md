# Working notes — e64c021e29ad

## 2026-10-11 — assignment review-1157018345b33d45

Selected generator version: **3.0.1**. Final generator SHA-256: `8349541496f9d16301ab6cf614b39758d4f6ea5a8f8d4fc8b8fa7f5ce39dad0a`. The selected canonical Racket rule is unchanged and pinned as `RULE_HASH="69a4bb5ee756"`; no authority, catalog approval, or training-safety record was changed.

### Intended rule

Each 4-connected object in colors 5–9 has one adjacent code cell. Code 1 means sweep up, 2 right, 3 down, and 4 left. Remove the code cells. Starting from every original object cell, paint a ray in the object's color in the coded direction through the edge of the grid. Sweeps are cellwise, not over the object's bounding rectangle.

### Reversed design choices

The selected baseline attached each code on the side matching its value. Prior return `review-642260c8f2368bc6-v0001` measured this shortcut on 1,488 objects across 900 generated grids. The revised sampler cycles attachment side independently of code and covers all 16 code/side combinations. For the explicit one-object override it also prevents the sole object's side from equaling its code, because a one-pair teaching example otherwise cannot refute the side-cue rival.

The baseline also left object color strongly coupled to direction and never used color 9 in the ordinary teaching distribution. The three labeled canonical pairs themselves admit the exact compact rival `5→left, 6→up, 7→down, 8→right`; color 9 is absent. The revised sampler deliberately violates that lookup, includes color 9 in every default input, and declares the rival for executable checking.

The baseline exposed non-varying/misleading `position_bias` and `density` controls, permitted degenerate texture modes, silently coerced dimensions, accepted unknown controls, lacked `RULE_HASH`, and supplied no semantic teaching contract. Version 3.0.1 exposes only observable exact controls (`grid_h`, `grid_w`, `n_objects`), validates their types and ranges strictly, and pins the canonical rule.

### Current curriculum choices

Ordinary inputs have two or three independently coded objects. The first has a code-specific concavity, and object sweep corridors are disjoint; this guarantees a visible disagreement with sweeping a full bounding box and prevents another object's trail from masking the witness. Every ordinary sample refutes the declared marker-side, object-color, bounding-box, ignore-color-9, largest-object-only, and fixed-up rivals.

Every fourth sample uses one of the three canonical `(height, width, distinct-input-color-count)` profiles: `(9,10,5)`, `(10,11,5)`, or `(12,12,7)`. The declared strict-profile floor is 25%; the final semantic panel measured 173/600 = 28.8%, and the profile-floor check hit every band. Four demonstrations are required. A 48-step deterministic lesson schedule is declared and separately enumerated at fixed seed 0.

### Verification summary

- 49/49 task-local tests pass. The retained TDD red run had 34 failures before implementation; a later regression first reproduced the one-object marker-side tie.
- The final semantic panel checked 600 draws: all five witnesses fired 600/600, all five witness/rival claims were verified, 12/12 sampled lessons were identifiable, and 0/60 query rotations were ambiguous.
- Fixed-seed schedule enumeration materialized 144/144 lesson starts and 720/720 rotations with zero ambiguities, hook warnings, or scoring errors.
- The production census materialized 300/300 lessons (100 per band) and 1,500/1,500 rotations, with zero ambiguities and 1,500 unique inputs.
- The post-repair visible-only solve matched all four demonstrations on its first revision. It is an exposed solve because the reviewer had already studied the rule.

### Known limits and open status

The public grid domain is deliberately bounded to 9–16 rows, 10–20 columns, one to three objects, 2×2-scale connected shapes, distinct object colors, and nonoverlapping sweep corridors. Explicit `n_objects=1` is supported, but ordinary lessons use at least two. The strict-profile definition is a size/palette-count proxy, not a replay of canonical layouts.

Declared-rival and finite schedule checks do not prove unique induction against every possible program, every seed, or every rejected-pair schedule. The 48-step enumeration is complete only for seed 0 and the three named difficulty bands. No downstream model was trained, so no learning gain is claimed. The full after battery records a strict semantic-stage warning solely because that stage does not consume the separately required schedule-census receipt; the substantive semantic checks inside it pass, and the complete schedule receipt is retained separately. Catalog approval remains false and training safety remains unverified.
## Current reviewer considerations

Source SHA-256: `8349541496f9d16301ab6cf614b39758d4f6ea5a8f8d4fc8b8fa7f5ce39dad0a`.

# Decisions — e64c021e29ad

Assignment `review-1157018345b33d45`; selected implementation version 3.0.1. Baseline generator SHA-256 was `573a86ce4296aa4f8a551aee28cbe02c83631c4568a42025fdfadb4f3f7bb1f5`; final SHA-256 is `8349541496f9d16301ab6cf614b39758d4f6ea5a8f8d4fc8b8fa7f5ce39dad0a`. “Original rationale” below is limited to source comments or retained evidence; where none survives it is marked unknown.

## D1. Preserve and pin the selected canonical rule

**Original rationale:** the baseline summary described arrow-driven sweeps, and all three canonical labeled pairs agree with the selected Racket program. No retained evidence justified changing authority bytes.

**Choice:** keep the Racket rule unchanged and declare `RULE_HASH="69a4bb5ee756"`. The Python oracle is an independent executable spelling used for checks; Racket remains label authority.

**Alternatives considered:** alter the rule to infer direction from attachment side or color. Both fit some visible evidence but contradict the selected executable rule and generated counterexamples. Rejected.

**Probe and limits:** rule smoke, authority sync, all canonical pairs, and the exact question witness were checked through Racket. The catalog remains unapproved and training safety unverified.

## D2. Expose only exact, observable controls

**Original rationale:** unknown. The baseline advertised `position_bias` and `density` singleton/dead axes plus texture variants; dimension overrides were sampled through default bands rather than honored exactly.

**Choice:** expose only `grid_h=9..16`, `grid_w=10..20`, and `n_objects=1..3`. `observe_overrides` recovers them from pixels. Unknown names, booleans, floats, strings, and out-of-range values fail explicitly.

**Alternatives considered:** retain legacy aliases for compatibility; keep texture as a diagnostic axis; silently clamp impossible values. All would preserve a misleading public contract or make requested interventions non-causal, so they were removed.

**Probes:** the final override matrix evaluates 15,300 generated cases across all bands and declared values, including deterministic replay and invalid controls. Task tests cross boundary combinations. A single-object marker-side issue found by this matrix was reproduced by a red test and repaired.

**Limits:** controls are a bounded authoring contract, not an enumeration of every lawful rule input. `difficulty=None` follows the medium-like default distribution but remains independently deterministic.

## D3. Decouple marker attachment side from code value

**Original rationale:** the old implementation put each marker on the geometric side corresponding to its numeric direction. The reason was not retained. Prior return `review-642260c8f2368bc6-v0001` used this as an audit lead and measured equality for 1,488/1,488 objects over 900 grids.

**Choice:** cycle attachment side independently from code and cover all 16 `(code, side)` pairs. In an explicit one-object sample, rotate the side when it would equal the code, so that the one visible pair itself refutes “sweep away from the marker.”

**Alternatives considered:** random independent side only; global rotation of the old layout; rely on multi-example aggregation. Randomness would not guarantee per-sample or per-lesson teaching. Global rotation preserves equality. Relying on aggregation leaves held-out rotations vulnerable. The deterministic complete pairing was chosen.

**Probes:** `test_marker_attachment_is_not_a_direction_shortcut`, the single-object regression, semantic witness `marker_side_is_not_direction`, 600/600 witness hits, and both lesson censuses.

**Failure modes and limits:** attachment-side derivation in a concavity uses a deterministic adjacent-cell convention. The generator avoids ambiguous multi-owner markers and verifies exactly one marker per object.

## D4. Break the canonical object-color direction lookup and include color 9

**Original rationale:** unknown. Canonical examples happen to use a perfect mapping: color 5 left, 6 up, 7 down, 8 right; color 9 is absent. The baseline reproduced this correlation strongly enough to make it a plausible training shortcut.

**Choice:** schedule codes independently of colors, include color 9 in every ordinary default input, and declare `object_color_direction` as both a canonical shortcut and lesson competitor. Retain the exact generated counterexample under `counterexamples/object-color-direction-shortcut.json`.

**Alternatives considered:** recolor canonical layouts; uniformly permute every color including code values; merely add color 9. Recoloring risks changing literal code semantics. Permuting code values changes the rule. Color 9 alone would not break the 5–8 lookup. Rejected.

**Probes:** the rival fits all three labeled canonical pairs in the focused test, but every 20-case default panel disagrees; the exact Racket-checked 9×10 specimen is in `checks/question/`. All 300 production lessons and all 144 schedule starts refuted the rival.

**Limits:** the chosen color schedule is deterministic and finite. Other color-based hypotheses may exist; the evidence only refutes the declared lookup and checked competitors.

## D5. Teach cellwise sweep rather than bounding-box sweep

**Original rationale:** the canonical rule iterates original object cells. Some canonical objects are rectangles, so a full-bounding-box rival fits both canonical training demonstrations; the canonical test already contains a distinction, but generated training lessons still need one.

**Choice:** make the first ordinary object a code-specific concave shape whose missing corner lies on a distinguishing sweep line. Keep object sweep corridors disjoint so another object's paint cannot cover the witness cell.

**Alternatives considered:** use arbitrary concave shapes and rely on frequency; add an explicit shape axis; compare only against the canonical test. Frequency did not guarantee complete lessons, another public axis was unnecessary, and the test is not a training demonstration. The constructive witness was selected.

**Probes:** a first implementation passed most tests but failed six cases because another trail covered the missing-corner difference. The revised disjoint-corridor placement made the regression green. Witness `cellwise_not_bounding_box` fires 600/600, and all enumerated lessons refute the rival.

**Limits:** only 2×2-scale shapes are sampled. The design distinguishes the named bounding-box rival; it does not exhaust all possible morphology shortcuts.

## D6. Preserve canonical profiles without preserving canonical shortcuts

**Original rationale:** the baseline had no reliable canonical profile support and the profile-floor check was advisory. Exact historical mixture rationale is unknown.

**Choice:** every fourth sample uses one of three linked canonical profiles `(9,10,2 objects)`, `(10,11,2)`, `(12,12,3)`, while still applying all anti-shortcut witnesses. Declare a 25% strict-profile floor.

**Alternatives considered:** replay canonical grids; make all samples canonical-sized; sample dimensions uniformly only. Replay would overfit layouts, all-canonical would narrow diversity, and uniform-only missed the required profile floor. The linked quarter schedule balances support and variation.

**Probes:** 173/600 strict hits (28.8%), all 3/3 canonical inputs accepted, and profile-floor passes in easy/medium/hard.

**Limits:** `strict_canonical_like` checks dimensions and distinct input-color count plus structural validity. It is not a semantic distance metric to canonical examples.

## D7. Make teaching sufficiency executable and rotation-safe

**Original rationale:** the baseline had no `SEMANTIC_WITNESSES`, rivals, `lesson_identifiable`, or declared example requirement.

**Choice:** require four demonstrations; declare six lesson competitors and five witness/rival pairs; make every ordinary sample itself refute each competitor. Declare a 48-step schedule and test every cyclic start and every held-out query position.

**Alternatives considered:** two demonstrations; probabilistic witness frequency; ordered-only lessons. Two examples and mere frequency can leave plausible rivals alive. Ordered-only curricula are more brittle. Four examples plus per-sample witnesses make all rotations safe for the named rivals.

**Probes:** semantic smoke: 12/12 lessons identifiable and 0/60 rotations ambiguous. Production census: 300/300 lessons, 1,500 rotations, 0 ambiguities. Fixed schedule: 144/144 starts, 720 rotations, 0 ambiguities.

**Limits:** finite declared rivals are not a universal identifiability proof. Schedule enumeration is fixed seed 0 only. The after battery's semantic stage exits 1 because it requires a separate period enumeration but cannot ingest that completed receipt; this checker-integration limitation is documented rather than hidden.

## D8. Use constructive placement with strict validation

**Original rationale:** the baseline used looser generation and texture-specific exceptions that yielded malformed/ambiguous grids. Rationale for those exceptions is unknown.

**Choice:** enumerate legal object/marker placements; require distinct colors, one 4-connected object per color, one adjacent code per object, one owner per code, in-range ARC values, bounded dimensions, and disjoint object sweep corridors. Reject malformed grids diagnostically without throwing from `self_check`.

**Alternatives considered:** rejection sampling with high retry caps; repair malformed draws after generation; permit overlapping sweep corridors. Retry caps complicate exact overrides, post-hoc repair can change requested semantics, and overlap masked a required witness during TDD. Constructive placement was retained.

**Probes:** destructive mutation fixtures, deterministic replay, 49 task tests, self-check stage, override matrix, distribution/diversity checks, and the Racket-checked exact witness.

**Limits:** disjoint sweep corridors narrow compositional interactions. This is deliberate for transparent teaching, not a claim that overlapping sweeps are illegal under the abstract rule.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ece91eb901feb51a:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8349541496f9d16301ab6cf614b39758d4f6ea5a8f8d4fc8b8fa7f5ce39dad0a`. At disposition, audited bytes match the current source.

### Current decision

Bounded reviewer-reported audit of SHA 8349541496f9d16301ab6cf614b39758d4f6ea5a8f8d4fc8b8fa7f5ce39dad0a: source/semantic/override/schedule inspection and 49/49 task tests, zero skips, found no new issue. No new approval, closure of other findings, universal guarantee or maintainer execution implied.

### Assessment or prior finding

## e64c021e29ad

**No issue found** on the assigned current source SHA-256
`8349541496f9d16301ab6cf614b39758d4f6ea5a8f8d4fc8b8fa7f5ce39dad0a`
and rule hash `69a4bb5ee756`.

I inspected the current generator, its retained repair notes, semantic rivals,
exact override handling, and schedule tests. In particular, I checked the
previous marker-side shortcut repair, independent code/side/color/bounding-box
rivals, all 16 code-side pairings, the single-object case, and the task-local
coverage of all 48 schedule starts and query rotations. The portable audit-phase
task-test run passed 49/49 tests with no skips; see
`checks/audit/e64c021e29ad-task-tests/result.json` and
`checks/audit/e64c021e29ad-task-tests/checks/task_tests.xml`.

This is a bounded finite review, not proof against every possible rival. No
source was edited because this is a findings-only audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## Native parametric main — review-f51d0519a65e067f

The reviewer retained the exact selected canonical program as the default
`{"sweep_mode":"all"}` setting and added one nearby matched-input setting,
`{"sweep_mode":"first_hit_relay"}`. In the relay, the singleton color-9
object is a probe: its code supplies a ray, the first color-5..8 object hit by
that ray is the input-dependent intermediate, and that selected object's own
adjacent code supplies the second-stage sweep direction. The final output paints
the probe path in 9 and sweeps only the selected object. The target, color, and
second-stage direction cannot be fixed before the trace result.

Generation is deterministic and supports 2–6 demonstrations plus 1–4 queries.
Inputs are identical across settings, all episode inputs are distinct, and the
fourth query is a substantive 30×30 scene. Target colors vary across visible
demonstrations; a nearer off-ray object, a farther on-ray object, independent
marker placement, and perpendicular target direction jointly refute the finite
last-hit, nearest-object, probe-direction, path-only, no-path, fixed-target,
direct-all, marker-side, color-direction, ignore-9, largest-only, fixed-up, and
bounding-box hypotheses used in the task-local audit. Some rivals can fit one
example (the bounding-box rule fits the first seed-17 direct demonstration) but
are rejected by the visible lesson; no universal uniqueness is claimed.

`last_hit.rkt` is the wrong-intermediate counterfactual. On the retained 30×30
case the correct trace selects color 7 with code 3, while the farther hit is
color 6; protected execution changes the final grid. The native witness is at
`checks/e64c021e29ad/causal/witness.json` and has status `reviewer_replayed`.

Verification retained for this source:

- 75 isolated task tests passed, including the 49 existing canonical tests and
  26 new parametric/portable-Racket tests.
- The bounded authoring verifier exercised 8 episodes, 54 labels, and 82
  protected-Racket evaluations over seeds 0/17, demonstrations 2/3/6, and
  queries 1/4.
- Native qualification passed 2 settings × 2 seeds with 3 demonstrations and
  4 queries; default program SHA-256 remains
  `69a4bb5ee7560cebdd103908ba0eb4266ad187b5edfa2b9e9dce5a4f3e4fa2d6`.
- Public projection checks show that settings, programs, and query answers do
  not affect public bytes, and first-turn bytes match single-query use.

During witness construction, the strict whole-expression parser found one extra
closing parenthesis in each newly authored noncanonical Racket source. The normal
rule wrapper had evaluated the first expression and ignored the suffix. Both
sources were corrected, a strict parser regression was added, and manifest,
authoring evidence, qualification, and witness were regenerated on the corrected
bytes.

Status is reviewer **ready**, not accepted. The owner must integrate the exact
patch, rerun native qualification/acceptance, and separately decide training
admission. Optional peer targets `637229802e6f` and `b2d6e6b60917` were left
unchanged; effort was concentrated on completing and adversarially checking the
complex MAIN deliverable.
