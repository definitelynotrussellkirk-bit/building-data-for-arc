# Current working notes: b19deac47327

## Rule and authority

Version **2.1.0**; generator SHA-256 `a839ebd14cca90ceeba69e541ea1df87d0e6c8eab9f5e5c01cf01356859efa3f`; canonical rule pin `2b2e46dd36cc`.

Exactly one opposite border pair is solid in two distinct colors other than 0 or 1. Each color-1 marker stamps the corresponding border color in the adjacent background cell toward that border. The first/top-left side is selected by `2 * axis < extent`; an odd-axis center therefore belongs to the first side. This review changes neither the canonical ledger nor the selected base program. Existing archival `raw_code` divergence remains historical, with selected executable synchronization verified.

## Current generator contract

The eight exact observable axes are `grid_h`, `grid_w`, `orientation`, `marker_count`, `edge_pair`, `side_balance`, `edge_marker_mode`, and `midline_marker`. Unknown keys and invalid overrides are rejected. Version 2.1.0 additionally requires literal integer seeds and nonnegative literal integer sample indices: booleans, floats, strings, and `None` cannot alias valid calls. Signed integer seeds remain deterministic.

The four-slot schedule retains `cross_horizontal`, `tie_vertical`, `cross_vertical`, and `tie_horizontal`. Three ordered demonstrations precede one query; any holdout from a complete four-pair block is supported against the eight declared competitors. Crossed canonical shape/orientation anchors remain exactly 12×10 horizontal and 12×13 vertical. Tie profiles now draw dimensions from keyed choices:

| Profile | Height choices | Width choices |
|---|---|---|
| `tie_vertical` | 12–16 | 11, 13, 15, 17 |
| `tie_horizontal` | 13, 15 | 10–18 |

These choices broaden ordinary size support while preserving an odd projection axis, both sides, unseen orthogonal-edge markers, and the strict canonical envelope. Explicit dimension overrides retain their existing 9–18 domain. Difficulty changes marker-layout randomness while preserving the declared profile axes.

The independent parser, `observe_overrides`, Python rule mirror, strict profile predicate, seven semantic witness families, rival registries, and `lesson_identifiable` remain active. Historical shortcut grids in `counterexamples/canonical_shortcuts.json` retain their original version 2.0.0 source identity; tests validate their labels against the unchanged rule. New rejected-call examples are in `counterexamples/invalid_call_arguments.json`.

## Current verification

All counts below bind to the generator hash above in return `review-9ff8ca4fa3be7164`:

- Full final battery: 12/12 green, with required query rotations and a source-bound schedule census (`checks/after-final/`).
- Portable task suite: 40/40 passed, including 17 sampling regressions and 14 parametric tests (`checks/task-tests/`). The sampling regressions first produced 16 failures and one pass on the baseline; both runs are retained.
- Override matrix: 849 cases × 30 seeded draws × three bands = 76,410 accepted, zero findings or rejections.
- Semantic sample: 600/600 strict; all four canonical pairs accepted; seven witness families fire and all seven rival claims verify.
- Profile floor: 30/60 exact profiles and 60/60 inside the envelope; exact hits by easy/medium/hard are 10/20, 12/20, and 8/20.
- Broad census: 100 lessons per band, three demos plus one query, 1,200 unique inputs, zero production ambiguities in 300 lessons and zero ambiguities in 1,200 holdouts (`checks/lesson-census.json`).
- Fixed-seed schedule census: seed 0, all starts 0–3 and all three bands; zero ambiguities in 12 production lessons and 48 holdouts. Its overlapping windows contain 21 unique inputs (`checks/schedule-census.json`).

The broad census uses deterministic hash-derived seeds and consecutive starts 0–99. Its legacy `sampler.period=6` is a reporting bucket; the explicit schedule receipt binds the actual declared period of four. These are finite checks of declared hypotheses, not a proof against every possible shortcut.

## Parametric extension — proposed, not admitted

`workspace/parametric/prototype.py` implements four combinations of `distance ∈ {1,2}` and `odd_tie_side ∈ {first,second}`. Distance two stamps one cell two positions away and leaves a gap. The default emits the exact canonical program bytes, SHA-256 `18c042039414a6bd8745b9ffc3277879010959e3ce76d64d94d4d16925343dd8`. Other settings materialize separate Racket programs; actual Racket execution supplies every label.

Parameters are chosen once per seeded episode; inputs use an independent stream and a common lawful domain. Before drawing a query, all three demonstrations must uniquely distinguish the chosen setting among the four hypotheses. The suite checks 128 complete forced-setting episodes and 512 holdouts; CLI evidence includes all four seed-selected settings, exact instantiated programs, a common-input contrast, and an intentionally ambiguous teaching example. See `workspace/parametric/README.md` and `checks/parametric/` in this return.

This pre-query parameter test is conservative: indistinguishable tie settings can still agree on an even-axis query. The README documents that false-positive boundary. Variant evidence and the narrower collision-free sampler do not constitute production parametric API support or training approval.

## Provenance and unresolved limits

The accepted version 2.0.0 review `review-a8e2e34d9efd7169:v0001` (return SHA-256 `98448f3b29bc30fb439a72d6e11a515548b40a364fc60706aa55197e2d415417`) supplied useful leads; current results were rerun. Earlier audit `review-458dfac6a8c9102f:v0001` (return SHA-256 `08a35c1e539cfbe39c28a2d5e2315abb8cbf76997c6f218f586a4c2be2e55713`) concerns source `961d15d4ac81fe108f6ee1f2a11c534eeb6a48f20b229eb034bf12de6d812f18`. Its indexed status remains **needs_triage**; this return supplies current override evidence without rewriting or closing that record.

The fixed four-profile schedule retains incidental profile/color/count correlations despite broader dimensions. The prototype imposes two-cell clearance and one marker per orthogonal lane; that restriction and its finite four-hypothesis gate need separate distribution review before admission. The rule is contextual selection by orientation and marker side; no sequential or multi-operation composition claim is made.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-458dfac6a8c9102f:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `961d15d4ac81fe108f6ee1f2a11c534eeb6a48f20b229eb034bf12de6d812f18`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve the old source 961d15d4ac81fe108f6ee1f2a11c534eeb6a48f20b229eb034bf12de6d812f18 exact-size/unknown-key/rule-pin finding on accepted source a839ebd14cca90ceeba69e541ea1df87d0e6c8eab9f5e5c01cf01356859efa3f. Reported final override matrix covers849 cases and76410 accepted draws with zero mismatches/findings/rejections; strict call validation, RULE_HASH and authority-sync stages pass.40 portable tests repeat in a fresh358-file runtime closure. This addresses the old grid_h=18 ignored-control witness and missing pin; no owner rerun or universal correctness claim.

### Assessment or prior finding

## b19deac47327

**Classification: Reproduced defect.**  Generator SHA-256
`961d15d4ac81fe108f6ee1f2a11c534eeb6a48f20b229eb034bf12de6d812f18`.

The generator advertises exact `grid_h`/`grid_w` controls but accepts and ignores
them.  At seed 0, sample 0, easy, `grid_h=18`, it returned a 7x7 grid and
`self_check` returned no error.  The complete minimized witness, input, command,
and hashes are in `checks/audit/b19deac47327/override_counterexample.json`; the
reusable probe is `checks/audit/b19deac47327/probe.py`.

The shared override checker independently failed: 115,110 attempted draws,
90,390 accepted, 24,120 explicit rejections, and 86,714 findings.  Of these,
72,027 are requested/observed mismatches and 13,500 are self-check findings; an
unknown override key is also accepted.  Evidence:
`checks/audit-b19deac47327-override/checks/b19deac47327_after_override_results.json`.
Defect lint additionally reports ordinary/degenerate `texture` overlap, no
`RULE_HASH` pin (current hash `2b2e46dd36cc`), and a behavior-equivalent archival
rule-text divergence:
`checks/audit-b19deac47327-defect_lint/checks/b19deac47327_after_defect_lint.log`.

No fix was applied because this was an audit-only target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-458dfac6a8c9102f-v0001/audit_assets.json), manifest SHA-256 `d740736098c5c49126b6cab4c39e891ce1b79b8a768b1070b51ec4fd2baca1bd`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `a839ebd14cca90ceeba69e541ea1df87d0e6c8eab9f5e5c01cf01356859efa3f`.

# Decisions — b19deac47327

Selected version: **2.1.0**. Final generator SHA-256: `a839ebd14cca90ceeba69e541ea1df87d0e6c8eab9f5e5c01cf01356859efa3f`. Canonical rule pin: `2b2e46dd36cc`. Paths below are relative to `WORK/`.

## D1 — Require literal integer call arguments

The issued v2.0.0 source accepted Boolean, fractional, string, and other invalid seed/index values; negative indices wrapped around the curriculum. Its rationale for permissive arguments was undocumented. `generate` now requires `type(seed) is int` and `type(sample_index) is int`, with a nonnegative index. Negative integer seeds remain valid because they are legitimate deterministic identities.

Silent conversion was rejected because it changes the caller's request. An `isinstance(..., int)` check would still admit booleans. Existing exact override validation remains intact. Evidence: `repo/generators/b19deac47327/counterexamples/invalid_call_arguments.json`, `repo/generators/b19deac47327/tests/test_sampling_contract.py`, and `checks/sampling-regressions/receipt.json` record 16 failures/1 pass on the baseline and 17 passes after repair.

## D2 — Broaden tie-case dimensions while retaining the teaching schedule

Fixed tie grids preserved useful witnesses but restricted default heights to 12–13. The repair keeps the crossed anchors `(12,10)` horizontal and `(12,13)` vertical. Keyed default draws now give `tie_vertical` heights `{12,13,14,15,16}` and widths `{11,13,15,17}`; `tie_horizontal` heights `{13,15}` and widths `10..18`.

These choices retain odd projection axes, unseen orthogonal-edge markers, canonical-envelope support, and at least two exact canonical-profile anchors per block. Any holdout from four consecutive slots still has three demonstrations covering both orientations and the declared shortcuts. Independently randomizing every profile or widening beyond the canonical envelope would weaken those guarantees. Explicit dimension overrides retain their existing `9..18` domain.

Evidence: `checks/schedule-census.json` covers 12 fixed-seed lessons and 48 holdouts; `checks/lesson-census.json` covers 300 production lessons and 1,200 holdouts, with no declared-rival ambiguity. These are finite checks, not universal induction proofs.

## D3 — Preserve authority and historical provenance

The selected canonical Racket program and original reasoning remain unchanged: identify opposite colored borders, locate markers, choose the appropriate half, and project the border color one cell. No rule rewrite was necessary. The authority receipt is `checks/after-final/checks/b19deac47327_after_authority_sync.json`.

`repo/generators/b19deac47327/counterexamples/canonical_shortcuts.json` remains bound to v2.0.0 source `e8eeb4702e21c23fbb5e01c317b5e8f27462f303295b0aa0c39ba9e00e94bd70`. Its test now asserts that historical identity explicitly while rechecking the witnesses. Relabeling old evidence as newly generated by v2.1.0 was rejected.

Prior return `review-a8e2e34d9efd7169:v0001`, archive SHA-256 `98448f3b29bc30fb439a72d6e11a515548b40a364fc60706aa55197e2d415417`, informed the review as a lead only. Its reviewer-reported claims do not substitute for current measurements; its identity is retained in the generator's `evidence/review_index.json`.

## D4 — Keep the four-setting extension separate and label it through Racket

The proposed `repo/generators/b19deac47327/workspace/parametric/prototype.py` varies `distance` over `{1,2}` and `odd_tie_side` over `{first,second}`, chosen once per episode. Distance two stamps one offset cell; it does not fill a line. The default `(1, first)` returns the exact canonical program bytes. This retains the original object roles and reasoning, unlike adding unrelated transformations.

All four settings share an input sampler with two-cell clearance and at most one marker per lane. The sampler does not receive the parameters, preventing a parameter-specific input giveaway. This common domain is deliberately narrower than canonical support. Racket authors labels and rival predictions; the Python oracle is test-only.

Public exports contain demonstrations and query inputs only. Seeds, parameters, programs, proofs, and query labels remain authoring data. Evidence: `checks/parametric/all-settings/summary.json`, `checks/parametric/all-settings/manifest.json`, and `checks/parametric/all-settings/private/shared-input-contrast.json` record four settings, four distinct outputs on one input, and 16 holdout checks.

## D5 — Require parameter identification before drawing the prototype query

The prototype admits an episode only when its demonstrations leave exactly the chosen parameter setting alive, before requesting a query. Two odd-center witnesses in each four-phase cycle make this condition constructive for ordinary episodes and all held-out-pair choices. An intentionally even-only lesson is rejected with `AmbiguousLesson`; replacing one demonstration with an odd witness repairs it.

This gate is conservative. Even-only demonstrations can leave both tie settings alive while an even-axis query has the same answer under both. Rejecting that case is a false positive for answer ambiguity, although the parameters remain unidentified. A query-conditioned policy could admit all surviving hypotheses when they agree on the actual query. That alternative is proposed, not implemented.

The odd-query failure, repaired lesson, and harmless even-query boundary are retained in `checks/parametric/all-settings/private/teaching-counterexample.json`. They are constructed teaching cases, not model-solve failures.

## D6 — Offer passive preparation diagnostics as a separate tool patch

`checks/tooling/prepare-diagnostics/prepare-diagnostics.patch` proposes safe post-failure diagnostics without installing a shared-code change. It reports typed worker status and isolated prerequisite discoverability, while excluding worker stderr, rules, labels, and private error text. Exposing raw exceptions or changing the assignment/seed was rejected.

The proposal preserves the original blocked result even if its diagnostic probe fails. Discoverability is not successful import or execution, and this work does not identify the original preparation failure's cause. Synthetic regressions plus existing visibility tests total **19 passes** after patch application; commands, hashes, genuine red runs, and limits are in `checks/tooling/prepare-diagnostics/evidence.json` and `checks/tooling/prepare-diagnostics/replay.json`.

## D7 — Retain unsuccessful checks and distinguish current verification from replay

Baseline failures and development mistakes remain evidence. The first after run, `checks/after/result.json`, lacked the required schedule-enumeration receipt; its semantic warning was `declared_period_not_enumerated`. Passing smoke lessons and rotations did not satisfy that separate requirement. Suppressing the warning or describing the run as fully green was rejected.

The same generator bytes passed **12/12 stages** once the source-bound census was supplied: `checks/after-final/checks/b19deac47327_after_battery_summary.json`. Portable staged tests passed **40/40**, with zero failures/errors/skips in `checks/task-tests/checks/task_tests.xml`. Parametric setup failures and corrected runs remain under `checks/parametric/`; they are distinguished from expected missing-feature tests.

Fresh patch replay subsequently verified all nine changed files byte-for-byte in the declared 358-file runtime closure of the 94,130-entry original archive. A separate public task stage in that checkout's own virtual environment and bundled Racket runtime passed all 40 tests again; actual isolated runtime `/tmp/arcpuzzles-check-jvujdbce`. `checks/replay/verification.json` and `checks/replay/task-tests/result.json` retain scope, paths and results. Final packaging retains source patch SHA-256 `f68342fe091fa8a3eaa53bdab111f7be4fd2baeee39ba7d06562cc905c5fe351`. The diagnostics-patch replay in D6 remains a separate result.

## D8 — Preserve audit boundaries and reserve approval for the owner

The two newly assigned targets were findings-only. Their sources remain unchanged; concrete production ambiguities and Racket-backed reproductions are documented in `checks/audit/0d03b427c121/section.md` and `checks/audit/37348ddf20d0/section.md`. Applying fixes to those targets would exceed this repair's scope.

The inherited audit `review-458dfac6a8c9102f:v0001`, archive SHA-256 `08a35c1e539cfbe39c28a2d5e2315abb8cbf76997c6f218f586a4c2be2e55713`, concerns source `961d15d4ac81fe108f6ee1f2a11c534eeb6a48f20b229eb034bf12de6d812f18` and remains `needs_triage` in `repo/generators/b19deac47327/evidence/review_index.json`. Neither new bytes nor passing checks automatically close that record.

This return proposes the selected repair, a separate parametric prototype, and a separate diagnostics patch. It does not grant source approval, variant approval, or training admission.

## Current alternate projection-span proposal

Unselected older-baseline proposal, not a current repair. Issued baseline e8eeb470/version2.0.0 differs from installed approved a839ebd1/version2.1.0 accepted in review-9ff8ca4fa3be7164. Current source already validates literal integer seeds/nonnegative indices and samples broader tie dimensions; applying this patch would replace newer source and the current four-setting distance/odd_tie_side prototype. Retain the distinct contiguous projection_span1/2 alternative: span2 paints both adjacent cells, whereas current distance2 stamps only the second cell and leaves a gap. Reviewer reports final enumerated12/12 battery,50 portable/fresh tests,300 lessons/1200 rotations with zero declared-rival ambiguity; ordinary after11/12 remains an intermediate enumeration-policy failure. Alternate prototype has2 episodes/eight holdouts and canonical parity on4 pairs, only seeds20/21 and a two-cell-clearance domain. No selected source/rule/prototype replacement, current prototype increment, approval or training admission. Runtime claims remain reviewer-reported; owner checks source/file bindings only. Retained at `workspace/proposals/review-5f511cd613054229/manifest.json`.

## Current alternate projection-depth proposal

Unselected older-baseline alternative. Issued e8eeb470/version2.0.0 differs from selected approved a839ebd1/version2.1.0 accepted in review-9ff8ca4fa3be7164. Current source already rejects malformed seed/index scalars,has broader tie-case height/width sampling,and includes a four-setting distance/odd_tie_side prototype. Replacing it with proposed14284b3b would overwrite newer decisions and that current prototype. Retain source delta and canonical-shortcut provenance rebinding separately; do not reattribute old counterexamples to current bytes. Reported proposed-source12/12 enumerated battery,25 portable tests,76410 accepted override draws and300 lessons/1200 rotations without declared-rival ambiguity remain source-bound. Two-setting projection_depth1/2 prototype has22 Racket applications,four canonical replays and two complete episodes with no surviving parameter rival. This is an alternate implementation on bounded inputs,not new current coverage. No selected source/rule/prototype replacement,approval upgrade,owner submitted-code execution or training admission. Retained at `workspace/proposals/review-130c73f761fc7a0a/manifest.json`.

## Retained export portability limit

The retained private source identity still pins earlier `shared/runtime/puzzle_generators/rule_wrap.py` bytes. Its export is preserved unchanged and was excluded from the current reviewer packet after the existing inventory guard rejected the changed dependency. Curate the historical export and its exact dependency closure before including this task in a later packet; this does not change generator approval or qualify the export against the current wrapper.

## 2026-10-24 review-f4bbc5c710b4b80e — native `finish_rule` family

This review leaves the approved production generator and canonical ledger
unchanged and replaces the older exploratory parametric workspace with a native,
source-bound two-setting family:

- `project_only` executes the exact selected canonical Racket bytes.
- `project_then_bridge` first performs canonical border projection, then groups
  the new interior border-colored seeds by aligned row/column and color, selects
  the unique maximum-count group, and fills its endpoint span.

The constructive sampler supports 2–6 demonstrations and 1–4 independently
revealed queries. Inputs are matched across settings and do not depend on the
hidden setting. Four stored queries use 13×15, 18×22, 24×27, and 30×30 grids;
the final case has substantive content touching all four boundaries. Each scene
contains a maximum-count winner, a wider lower-count distractor, and a narrower
gapped lower-count distractor, preventing count, span, first-found, and
single-border shortcuts from replacing the intended interaction.

The task-local protected-Racket audit checked both settings at seeds 0 and 17
with 2, 3, and 6 demonstrations and four queries. All labels matched, both
settings were uniquely identified from demonstrations alone, and nine executable
shortcut programs were rejected in 264 evaluations. Native qualification then
executed two settings × two seeds with two demonstrations and four queries: four
jobs and 32 protected-Racket evaluations. A second qualification run produced
byte-identical `qualification.json` and `execution.json` receipts.

The sequential witness names A as canonical projection, the intermediate as the
projected grid plus its aligned seed groups, and B as maximum-count group
selection plus bridging. On the retained 30×30 case, replacing A with the
`skip_projection.rkt` counterfactual removes the eligible interior seeds and
changes the final output. The owner-replay witness passed.

Current evidence is under `checks/b19deac47327/`, including the source inventory,
public-projection check, native qualification, replay, and causal witness. This
is reviewer-ready evidence only. Owner source integration, native acceptance,
and any training-admission decision remain outside this return.
