# Working notes: 40ad7195c775

## Current rule and source identity

Infer the modal background, the endpoint color appearing exactly twice, the high-frequency stripe color, and the waypoint color. Normalize vertical stripe scenes by transposition. Starting below the upper endpoint, draw an endpoint-colored staircase: descend to one row above each ordered stripe, move to the middle cell of its waypoint run, punch through, and finally hook to the lower endpoint while preserving all non-route cells.

Selected generator version: `3.1.0`. Final review SHA-256: `d5bec27143b675aa8bd44e42eb13e477571d75781ac0ce0035af3fe011dfa95c`. Canonical Racket authority is unchanged: `RULE_HASH=1482fe487ae4`.

## Review decisions (2026-10-21)

- Prior current note `GNOTE-000056` was used as a lead only; the pinned baseline was remeasured.
- Reversed permissive scalar handling: `seed` must be a literal integer; `sample_index` must be a literal nonnegative integer. Negative integer seeds remain supported. This fixes 15 baseline strict-scalar warnings.
- Added an explicit canonical-fitting shortcut, `canonical_profile_lookup`, plus a `generalized_geometry` witness and a three-demonstration lesson-identifiability contract.
- Retained exact shortcut counterexample: `counterexamples/canonical-profile-lookup-generalized.json`, recipe `generate(123, 9, scene_code=12096)`, intended versus rival difference 56 cells.
- Declared lesson policy: 3 demonstrations and 1 query, consecutive production samples. Final census: 300/300 production lessons and 1,200/1,200 required query rotations had no ambiguity against the declared rival; finite evidence only.
- Proposed, but did not select, the episode-level `waypoint_choice={left,middle,right}` prototype under `workspace/parametric/`; canonical/default is `middle`.

## Assumptions and known limits

- The selected generator still depends on the original frequency-role grammar and 30×30 stripe-family geometry.
- The semantic contract addresses the strongest declared profile-memorization rival, not all possible rules.
- The parametric prototype is not catalog-approved or training-admitted; retained evidence covers seeds 0, 1, and 2.
- The immutable inherited root test still uses a fixed-depth canonical-data path. Portable task-test preflight is blocked until maintainer migration; the fixture was not edited.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d5bec27143b675aa8bd44e42eb13e477571d75781ac0ce0035af3fe011dfa95c`.

# Decisions for 40ad7195c775

## Context and prior lead

I used current note `GNOTE-000056` only as a lead. It described the accepted baseline source `2cc152a3228cc7ec564d82ab0526ba1bcb1190091ccee41c9feadc02ded4d212`, its broad geometry/palette work, and the unchanged canonical rule. I remeasured the pinned source rather than treating those historical claims as current verification.

## D1 — preserve the rule and repair the call contract

**Prior choice:** `generate` relied on Python's permissive integer behavior, so booleans and negative sample indexes entered the schedule.

**New choice:** require `type(seed) is int`; require `type(sample_index) is int` and `sample_index >= 0`. Negative integer seeds remain valid because they are deterministic schedule inputs, while negative sample indexes are outside the public contract.

**Why:** the before defect lint produced 15 reproducible `strict-scalar` warnings. The smallest root-cause repair is validation at the public entry point, not downstream coercion.

**Alternatives rejected:** coercing values with `int(...)` would continue accepting booleans and numeric strings; rejecting negative seeds would unnecessarily remove deterministic support not identified as defective.

**Probe and failure mode:** focused parameterized tests cover booleans, floats, strings, negative sample indexes, and a valid negative seed. The after defect lint reports zero flags. Future additions must not bypass the entry-point checks.

## D2 — model the strongest canonical shortcut explicitly

**Choice:** declare `canonical_profile_lookup`, which applies the intended transform only to the four public geometry profiles and returns every other input unchanged.

**Why:** it fits all 8 labeled canonical occurrences yet disagrees sharply on lawful generalized scenes. It is stronger and more realistic than simple identity/flip/rotation rivals because it can memorize the full canonical support while failing to learn the generative rule.

**Witness:** `generate(123, 9, scene_code=12096)` is lawful, non-public-profile geometry. The intended and selected Racket outputs agree, the lookup rival returns the input, and the outputs differ at 56 cells. The exact grids and final generator hash are retained in `repo/generators/40ad7195c775/counterexamples/canonical-profile-lookup-generalized.json` and `checks/shortcut-witness/racket.json`.

**Limit:** this finite rival does not exhaust all plausible shortcuts. Undeclared ambiguity remains unknown.

## D3 — require a three-demonstration teaching contract

**Choice:** `EXAMPLES_NEEDED = 3`; each lesson has 3 labeled demonstrations and 1 query. Production assembly uses consecutive sample indexes. `lesson_identifiable` validates each pair and requires at least one demonstration to refute `canonical_profile_lookup` for any query where that rival disagrees.

**Why:** correct individual labels do not make a lesson teachable. The canonical-only support leaves the lookup rule viable, whereas the production sampler normally includes generalized geometry.

**Evidence:** the semantic smoke test materialized 12/12 identifiable lessons and checked 48 diagnostic rotations. The larger required-rotation census materialized 300/300 lessons and 1,200/1,200 held-out rotations with no ambiguity against the declared rival, 0 materialization/scoring errors, and 1,194 unique inputs.

**Alternative rejected:** relying only on witness frequency would not guarantee that a complete lesson contains a refuting demonstration. A two-demo contract was also rejected because the assigned packet asks for a robust teaching schedule and the canonical/default floor is three.

**Limit:** the random census does not enumerate every seed or every possible rival. Its verdict is bounded to the declared contract and retained source hash.

## D4 — leave Racket authority unchanged

**Choice:** do not modify the canonical rule. Keep `RULE_HASH = 1482fe487ae4` and the authority set SHA-256 `5dedac8388fc8d8fc2f73cd4fab50eadd3a4190de065df8cc9f7e2c6c49bf320`.

**Why:** rule smoke, authority sync, canonical pairs, and the Python mirror already agree. The defects were public-call validation and teaching evidence, not transformation semantics.

**Failure mode:** any later rule change must regenerate authority-bound receipts and cannot reuse this review's battery checkpoints.

## D5 — prototype `waypoint_choice` as the bounded family parameter

**Choice:** choose one episode-level value from `left`, `middle`, or `right`. It determines which cell of every contiguous three-cell waypoint run the route punches through. `middle` is the canonical/default setting and its Racket source is byte-exact canonical.

**Why:** this changes one local rule decision while preserving the original object's roles, frequency inference, orientation normalization, stripe ordering, route construction, and output shape. The setting is inferable from demonstrations rather than encoded in the query.

**Alternatives rejected:** changing endpoint selection, stripe order, or route color would alter core object roles or the reasoning graph rather than provide a small family parameter. Varying orientation or palette is already input nuisance variation, not a rule parameter.

**Evidence:** seeds 0/1/2 cover all three settings; 9 training pairs and 3 queries are materialized; 36 protected Racket executions match the independent Python mirror; all 9 training pairs distinguish every setting. See `checks/parametric/waypoint-choice/private/manifest.json`.

**Status and limits:** proposed prototype only. It is not selected, catalog-approved, or training-admitted. Evidence is bounded to retained seeds and the declared left/middle/right rivals.

## D6 — preserve the immutable inherited fixture and report blocked

**Choice:** restore `tests/test_generator_40ad7195c775.py` byte-for-byte and report completion state `blocked`.

**Why:** the packet explicitly marks that root test as frozen. Its fixed-depth path fails the portable task-test preflight before pytest, and the packet assigns migration to the maintainer. Editing it would make a green aggregate by violating the assignment.

**Evidence:** final fixture SHA-256 `9f37ddcbcc780566e97c9d2918b053fdcb5bfa9e564d68d8157092f53b6b2586`; exact failure in `checks/task-tests-confirm/result.json`. The two new portable test files independently pass 19/19.

## D7 — retain compact, hash-restorable census evidence

**Choice:** keep the complete 53,395,265-byte lesson-census report as gzip plus a compact companion and explicit raw/compressed SHA-256 mapping.

**Why:** the raw JSON exceeded the return's evidence budget; deleting it would lose decisive query-rotation evidence. Deterministic gzip reduces it to 805,070 bytes while preserving exact restoration.

**Limit:** `lesson-census.summary.json` is a companion, not an independent rerun. The compressed full report is authoritative; restore it and verify the raw hash before detailed use.
