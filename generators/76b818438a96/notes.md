# Working notes: 76b818438a96

## Current intended rule

The input has exactly two same-color cardinal components that are simple, non-branching paths and exactly two singleton marker components. Each path has two endpoints and at least one bend. Exactly one endpoint has a unique marker on its outward ray through a clear zero corridor. If the marker is `d` cells from the endpoint, fill the `d-1` intervening cells with the path color and recolor the first `d-1` path cells from the opposite endpoint with the marker color. Four foreground objects use four distinct colors.

## Reversed decisions

The prior v3.0.0 choice modeled every path as a one-turn L. That was incorrect: canonical pair 2 contains a three-turn path, and canonical pairs collectively contain 1-, 2-, and 3-turn paths. Version 4.0.0 now validates and samples simple orthogonal paths with 1–3 turns and canonical path sizes `{7, 8, 12, 13, 16}`. Evidence: `tests/test_generator.py` and `workspace/reference_probe.py`; measured report: `checks/independent/reference-audit.json`.

The prior validator deliberately accepted all-background and singleton-only inputs as idle degenerates and advertised `texture=no_path`. That weakened the lawful domain and caused defect-lint/strict-call findings. Version 4.0.0 removes `texture`, rejects those impostors, rejects unknown or malformed calls, and exposes only three exact controls: `grid_h`, `grid_w`, and `palette_kind`. Minimal retained recipes are in `counterexamples/repaired_contract_regressions.json`; the focused tests cover the same cases.

The prior observer reported only object counts and could not recover advertised axes. Each palette label now maps to a distinct exact four-color set, and `observe_overrides` recovers all exact controls plus path sizes, turn counts, marker distances, and extension counts.

## Distribution and teaching choices

Dimensions cover 14–30 with deterministic canonical 20×20/30×30 support in each standard battery window. Path sizes cover the five canonical sizes. Marker distances deliberately include one near branch (2–3) and one far branch (4–7) in every draw. The near branch refutes the canonical-fitting `far_markers_only` shortcut, which incorrectly ignores markers closer than four cells. `EXAMPLES_NEEDED=3`, `MIN_STRICT_FRAC=1.0`, and `lesson_identifiable` checks the declared rival.

The selected Racket authority was not changed. The Python semantic mirror is diagnostic only; retained real-Racket parity checked 36 canonical/generated inputs with zero mismatches.

## Native parametric family — current decision

`workspace/parametric/adapter.py` and `promotion.json` expose the existing
`recolor_origin ∈ {opposite, aligned}` programs through the native API. The
canonical generator and Racket text remain unchanged. Use 2–6 demonstrations
and 1–4 queries independently, normally three/four. Inputs are matched across
settings; query prefixes are stable across counts. The default program is exact.

The first two demonstrations deliberately include a small 14×14 scene and a
substantive 30×30 scene; long paths and corridors grow with the canvas. This
reverses the old prototype's one-query default and small-only path vocabulary.
A capped-six-cell Racket rival fits two small demonstrations but differs on five
large-query cells. Replacing one small demonstration with the long example
repairs that lesson without increasing demonstration count. Every native
lesson checks 11 finite rivals from demonstrations against each query.

Native geometry rejects extra marker rays (even behind obstructions),
intersecting extensions and traversal saturation. The **unchanged canonical
sampler has a confirmed open defect** at seed 987076/index 76/hard: Racket picks
an obstructed extra ray and changes 24 cells versus its Python diagnostic rule.
The six-case probe and exact hashes are in the return's
`checks/76b818438a96/canonical-ray-probe/result.json`. Native sampling excludes
this case. A concrete repair is supplied in `workspace/canonical_ray_guard.patch`; its
source-bound probe reduces that regression from 24 differing cells to zero and
accepts all eight retained canonical inputs. It is a verified proposal, not
applied to the source qualified here. Next canonical action: apply that guard
and renew source approval plus native qualification;
do not silently claim the current canonical source is repaired.

The causal argument is A: construct the marker-bound extension plan/count;
B: use that count to walk/recolor the original path from the chosen endpoint.
The protected Racket intervention retains downstream changed original-path
cells, not merely changed extension paint. This is an input-dependent geometric
dependency, not iterative simulation.

Source/evidence inventory and native qualification accompany the return.
`ready` means owner exact-source acceptance remains pending after integration;
no training admission. Public files use exact visible-byte hashes. Full stored
query arrays are controller-side; first-turn projection/prefix checks do not
claim a downstream trainer was tested. Details and commands live once in the
parametric README.

## Known limits and open findings

The lesson census proves only the declared rival was refuted over the measured 300 lessons and 1,200 rotations; it is not universal identifiability against undeclared rules or all seeds. The random polyline sampler covers canonical discrete support but does not enumerate every possible path geometry. The native interface is now implemented; exact-source owner acceptance and downstream training admission remain separate.

Imported associated notes remain in `evidence/associated_notes.jsonl`. The prior return `review-0eac73c41930fb4b:v0001` was used only as a lead for the unknown-key and observer-contract findings; all final claims were remeasured against this packet.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0eac73c41930fb4b:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f6ef08e0e970521af8776f5c11afdc38cb662f49b7f72c7d14ee611bbd4a3210`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by accepted source 36333edb8162ad82300af823d21f9e0fd8e04852194a2f1336599dc41f428c42 based on reviewer-reported repair review-6f3ff7710f85ccdf:v0001. Version 4 rejects unknown keys, removes the unsupported texture axis and observes every retained exact axis. Focused regressions are generators/76b818438a96/tests/test_generator.py; the 49-test portable receipt is checks/task-tests/result.json and the independent checks/independent/reference-audit.json reports zero observer mismatches over 1000 draws. No owner rerun; later interrupted teardown receipts do not replace the completed task-test receipt. This does not resolve other audits.

### Assessment or prior finding

## 76b818438a96

**Reproduced defect — unknown override keys are silently accepted.** The audited generator SHA-256 was `f6ef08e0e970521af8776f5c11afdc38cb662f49b7f72c7d14ee611bbd4a3210`. At seed 0, sample index 3, difficulty `easy`, passing `__override_contract_unknown_axis__=123` returned a lawful-looking 20×20 grid rather than raising. The strict override stage therefore failed with category `unknown_key`; exact evidence is `checks/audit/76b818438a96/override/checks/76b818438a96_audit_override_results.json`, and the small independent reproducer is `checks/audit/76b818438a96/unknown_override_repro.py` / `.json`.

The same reproducer records a second contract inconsistency: `AXES` declares `grid_h`, `grid_w`, `palette_kind`, and `texture`, while `observe_overrides` returned only `n_paths` and `n_markers`. I did not assert that every advertised value is semantically dead because the full matrix accepted many legal combinations and explicitly rejected documented incompatible combinations; the source-bound actionable finding is the unknown-key acceptance and observer/declaration mismatch. No fix was made, as audit targets are findings-only.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-0eac73c41930fb4b-v0001/audit_assets.json), manifest SHA-256 `bde44daed828112b54eaabd4ebdb66c0b81e38d6bb99d0ed42e37a69091da485`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `36333edb8162ad82300af823d21f9e0fd8e04852194a2f1336599dc41f428c42`.

# Decisions for 76b818438a96

## D1 — Model the canonical object as a simple orthogonal path, not an L

**Prior choice:** v3 described and sampled only a corner with two perpendicular arms.

**New choice:** require exactly two one-cell-wide, connected, non-branching cardinal paths, each with two endpoints and 1–3 turns.

**Rationale/probe:** canonical geometry parsing found a three-turn path in pair 2 and two-turn paths in pairs 1–3. `workspace/reference_probe.py` checks degree signatures, endpoint walks, turns, and labels. Alternatives considered were retaining Ls for simplicity or accepting arbitrary connected shapes. The former excludes canonical inputs; the latter admits branches, loops, blocks, and ambiguous traversal. Failure mode: the random polyline sampler still covers only a subset of all legal simple paths.

## D2 — Cover canonical sizes while retaining controlled geometric breadth

**Choice:** sample path sizes from `{7,8,12,13,16}` and turns from 1–3, with band weighting rather than unrelated size ranges.

**Rationale/probe:** those are the complete observed canonical component sizes; 320 focused draws and the 1,000-draw independent audit cover all five sizes and all three turn counts. An unrestricted length range was rejected because it dilutes canonical support and makes profile-floor evidence weaker. Limitation: matching discrete sizes/turns does not match every canonical shape-frequency distribution.

## D3 — Use 14–30 dimensions with deterministic canonical profile slots

**Choice:** exact overrides permit 14–30; ordinary sampling is band weighted and every fifth index schedules 20 or 30, including a 30×30 slot.

**Rationale/probe:** canonical dimensions are 20×20 and 30×30, while smaller canvases add useful layout variation. Pure uniform sampling could miss exact profiles in a 20-draw band; canonical-only dimensions would overfit. The final strict profile-floor gate is green. Failure mode: deterministic index structure can itself be learned if raw sample indices leak, so sample indices must not be model-visible.

## D4 — Make palette controls exactly observable

**Choice:** retain four palette labels but map each to a unique exact four-color set: warm `(3,4,6,8)`, cool `(1,2,4,6)`, primary `(2,3,4,6)`, broad `(1,5,7,9)`.

**Rationale/probe:** four distinct foreground roles are required, and an observer must recover the requested exact axis. Overlapping/non-unique palette semantics were rejected because a returned grid could not certify which label was honored. Held-out `broad` expands colors without changing role logic. Failure mode: a model may exploit palette identity if lessons do not mix palettes; the 1,000-draw audit observed all four in every band.

## D5 — Remove idle degenerates and enforce a strict call contract

**Prior choice:** `texture=no_path`, all-background, and singleton scenes were treated as lawful no-ops; unknown keys and malformed scalar types were accepted.

**New choice:** expose only `grid_h`, `grid_w`, and `palette_kind`; reject unknown keys, booleans masquerading as integers, out-of-range values, invalid difficulty, all-background, singleton, straight, branched, looped, or otherwise malformed scenes.

**Rationale/probe:** the intended task is defined by two path/marker interactions. Idle scenes provide no rule evidence and mask misspelled controls. Minimal recipes are retained in `counterexamples/repaired_contract_regressions.json`; focused tests cover each behavior. Alternative: preserve degenerates as negative examples, but production sampling cannot label them as negatives separately, so they would become weak positive lessons.

## D6 — Force one near and one far marker per draw

**Choice:** marker distances are one value from 2–3 and one from 4–7; extension count is distance minus one.

**Rationale/probe:** all canonical markers are at distance 4–7, so `far_markers_only` fits every canonical pair. Near examples are a lawful extrapolation that directly refutes this shortcut, while a far example preserves canonical-scale evidence. Pure canonical distances were rejected because the shortcut remains untested; all-near distances were rejected as distribution drift. The 300-lesson census refuted the rival in every lesson and rotation. Limitation: this handles one explicit distance threshold, not every possible geometric rival.

## D7 — Declare three demonstrations and executable lesson semantics

**Choice:** `EXAMPLES_NEEDED=3`, `MIN_STRICT_FRAC=1.0`, executable witness/rival maps, and `lesson_identifiable` over `far_markers_only`.

**Rationale/probe:** three demonstrations preserve the packet's lesson budget, and because every generated pair contains a near witness, any nonempty demonstration set refutes the declared shortcut. The production census uses three demos plus one query and required rotations. Increasing to four was unnecessary for this rival; reducing to one would be more vulnerable to undeclared object-association rules. Limitation: finite rival declarations are not universal proof.

## D8 — Keep the selected Racket authority unchanged

**Choice:** patch only the generator, tests, notes, and workspace; pin `RULE_HASH=000a1e2b0988`.

**Rationale/probe:** canonical outputs and real-Racket parity already establish the rule. The defects were in input language, validation, control observability, and curriculum evidence. Changing the authority would add risk without repairing those causes. Final authority-sync and rule-smoke stages are green.

## D9 — Prototype only the smallest nearby rule parameter

**Choice:** `recolor_origin` has values `opposite` (canonical/default) and `aligned`; choose once per episode.

**Rationale/probe:** this changes exactly one relation while preserving paths, endpoint rays, extension length, marker cue, and traversal. Both exact Racket programs execute, and three demonstrations distinguish the settings in both retained episodes. Alternatives such as changing extension length, marker selection, or direction alter multiple reasoning roles and were rejected as less local. Limitation: no shared production parametric interface or approval is implied.
