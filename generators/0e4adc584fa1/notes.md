# Working notes: 0e4adc584fa1

## Baseline diagnosis

The pinned imported generator was version `1.4.1` (baseline SHA-256 `d37665ac7cd232e5f69c22f15fd48a2789540a8a92282b2d620b52aedfef1456`; retained as `workspace/generator-v1.4.1-before.py`). The interrupted before battery retained two green stages (`rule_smoke`, `dist_gate`), one advisory semantic stage with no contract, four failures (`lint`, `selfcheck`, `defect_lint`, `profile_floor`), and five not-yet-run stages.

Root causes, not just symptoms:

1. The canonical rule hash was not pinned.
2. Several advertised controls were dead or only nominal; exact overrides were not observationally testable.
3. Degenerate textures were mixed into the ordinary grammar.
4. `self_check` rejected lawful canonical symmetry rather than validating the actual Racket domain.
5. The distribution did not reliably retain canonical-size support in every band.
6. The five canonical examples encode a spurious canvas-size → control-code mapping, and the generator had no deterministic lesson schedule, rivals, witnesses, or lesson-level identifiability hook to refute it.

The prior associated evidence was used only as a lead. All current-source claims were remeasured.

## Repair design

Version `2.0.0` replaces the distribution but leaves the selected Racket rule unchanged. The grammar is intentionally narrow and observable:

- one isolated code cell in `1..4`;
- one 4-connected object using one to three colors from `5..9`;
- object bboxes in `3x3`, `3x4`, `4x3`, or `4x4`;
- a one-cell moat and marker wholly before or after the object in row-major order;
- six exact axes recovered by `observe_overrides`;
- unknown controls and invalid values reject instead of silently degrading.

The default code is `(seed + sample_index) mod 4 + 1`, so every four consecutive samples cover all four transformations. Four-sample groups share one canonical canvas size, directly breaking the canonical size→code shortcut. Band-aware object profiles retain canonical `3x3`, two-color morphology while adding lawful wide, tall, large, and palette-cardinality variation.

Hand-written object templates are 4-connected, span the promised bbox, and have four distinct quarter-turn orientations. An initial implementation included four 180°-symmetric templates; seed-local traces identified those exact templates, and only those templates were removed before final verification.

## Semantic contract

`rule_mirror` mirrors the selected law for diagnostics; Racket remains authoritative. Declared rivals cover identity-only, clockwise-for-all-nonidentity, reversed quarter turns, off-by-one turns, and the canonical size→code shortcut. Five witnesses exercise all four codes and size/code decoupling. `lesson_identifiable` checks labels, requires at least three code values after any one-pair holdout, and rejects a declared rival that fits all demonstrations but changes the query.

The claim is finite and relative to the declared rival class. It is not a proof that no other program can fit a lesson. `workspace/probe_curriculum.py` makes that limit explicit while exhaustively checking a small deterministic seed/start period and all query rotations.

## Regression workflow

Nine task-local tests were written against the pinned baseline first. Eight failed for the intended missing behavior; deterministic replay/global-RNG neutrality was already present. After the repair and the template correction, all nine pass. The tests bind the rule hash and all canonical pairs, four-code scheduling, exact controls, output sensitivity to the marker, canonical shortcut refutation, rotated-query identifiability, band profile support, determinism, and malformed near-miss rejection.

Imported associated notes retain their original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e9b1924c9d1b928ebb802dfe0ec1ac3e511acb75577003ad4f223bb99e6b147c`.

# Decisions and rationale

## D1 / R1 — Keep the selected Racket authority unchanged

**Choice.** Preserve rule hash `314b2cc8cd15`; repair only the selected generator, task-local tests, notes, and workspace tooling.

**Why.** The canonical outputs consistently implement “choose the last isolated 1–4 cell, remove isolated controls, crop the remaining foreground, rotate by the code.” The baseline `rule_smoke` was already green, and direct Python-mirror comparison matched all five canonical pairs. The defects were distribution, validation, provenance, and teaching defects rather than a wrong rule.

**Rejected alternative.** Simplifying the rule to require one marker or asymmetric shapes would silently narrow the authority and invalidate lawful canonical examples. The generator may enforce one marker for clean training inputs; the validator must still not claim canonical symmetry is illegal.

**Probe/failure mode.** Task test `test_rule_hash_and_every_canonical_pair_are_owned_and_mirrored`; final `rule_smoke` and `authority_sync`. Remaining limit: the Python mirror is diagnostic only; Racket remains authoritative.

## D2 / R2 — Replace nominal axes with six exact observable controls

**Choice.** Expose only `grid_h`, `grid_w`, `control_code`, `shape_profile`, `shape_colors`, and `marker_order`. Every control is recovered from the grid by `observe_overrides`; unknown keys and invalid values reject.

**Why.** The imported generator advertised controls that were dead, aliases, or not observable. Such metadata is worse than a smaller truthful grammar because lesson balancing and audits can believe variation exists when it does not.

**Rejected alternatives.** Keeping legacy names as silent aliases was rejected because it preserves untestable behavior. Keeping degenerate textures in the ordinary domain was rejected because empty/no-op scenes weaken the rule signal. A broader free-form object grammar was rejected because exact support and rotational ambiguity would be harder to verify.

**Probe/failure mode.** The exact override matrix passed the inherited override gate and 17 task-local cases in `checks/curriculum-probe.json`. Invalid combinations currently have no declared exceptions. Remaining limit: the four object-profile bboxes are deliberately bounded, not an attempt to cover every lawful connected object.

## D3 / R3 — Deterministically teach all four code branches

**Choice.** Schedule code as `(seed + sample_index) mod 4 + 1`; any four consecutive samples cover codes 1–4. A four-sample group shares one canvas size.

**Why.** Random code selection can create lessons missing a branch. More importantly, the five canonical pairs admit a spurious size→code table. Holding canvas size fixed while cycling all four codes refutes that shortcut in every ordinary four-demo lesson rather than merely increasing its eventual frequency.

**Rejected alternatives.** Pure random balancing and post-hoc rejection sampling were rejected as less reproducible and capable of leaving unlucky ambiguous lessons. Encoding code through marker location was rejected because it creates a second shortcut.

**Probe/failure mode.** The task tests check all four codes for multiple seeds, bands, and starts. `workspace/probe_curriculum.py` checked 480 consecutive windows and found the canonical shortcut refuted in all 480. Remaining limit: the schedule proves coverage only for consumers that preserve consecutive sampling; the production runner does, and the source-bound census records accepted indices.

## D4 / R4 — Retain canonical support while widening morphology

**Choice.** Use five canonical canvas dimensions in every band, retain frequent `3x3` two-color crops, and add `3x4`, `4x3`, `4x4`, plus one- and three-color objects. All templates are connected and span their advertised bbox.

**Why.** The baseline strict-profile failure showed the generator had drifted from the imported task. Canonical anchors make the generated distribution recognizable while added profiles prevent memorizing one crop geometry.

**Rejected alternatives.** Generating only exact canonical profiles was rejected as overfitting. Generating arbitrary sizes/colors was rejected because it would reduce profile-floor support and introduce unrelated domain complexity.

**Probe/failure mode.** Profile-floor passed canonical 5/5, exact-profile 60/60, and envelope 60/60 in the focused stage; final battery repeats it. Initial hand-written templates accidentally included four 180°-symmetric shapes. Seed-local orbit tracing isolated them; only those templates were removed. Remaining limit: canonical symmetric inputs remain validator-lawful even though ordinary generated crops intentionally have four distinct rotations.

## D5 / R5 — Separate domain validation from generated-example quality

**Choice.** `self_check` validates the documented structural domain and accepts lawful canonical symmetry. Generation adds the stronger four-orientation check after construction.

**Why.** A validator should not reject an authority-supported input simply because it gives weaker teaching signal. Conversely, generated lessons should avoid objects whose requested turns are observationally identical.

**Rejected alternative.** Enforcing asymmetry in `self_check` repeated the baseline bug and rejected canonical support. Omitting the generation-only orbit check would allow code branches with identical labels.

**Probe/failure mode.** All five canonical inputs pass; 56/56 destructive mutation fixtures were rejected in the focused self-check stage. Generated templates are checked with `_orbit_size(crop) == 4`.

## D6 / R6 — Add an executable finite semantic contract

**Choice.** Declare five rivals, five witnesses, rival-to-witness bindings, canonical shortcuts, and `lesson_identifiable`. The hook checks labels, requires at least three distinct codes after any one-pair holdout, and reports a rival that fits every demonstration but changes the query.

**Why.** Correct individual labels do not guarantee that a lesson teaches the intended rule. The canonical size→code rival is known to fit all five canonical pairs, so a distribution-level witness is required.

**Rejected alternatives.** A prose-only semantic note was rejected because gates cannot execute it. Claiming universal identifiability was rejected because any finite rival set is incomplete.

**Probe/failure mode.** The semantic gate verified 5/5 witnesses, 5/5 rival claims, 12/12 sampled lessons, and the size/code counterexample. The source-bound census materialized 300 lessons (100 per band), 1,500 query rotations, and found zero surviving declared rivals or hook warnings. `probe_curriculum.py` adds exhaustive small-period starts. Remaining limit: results are relative to declared rivals, not proof against every possible program.

## D7 — Test first and retain the failure evidence

**Choice.** Add nine task-local tests before implementation and preserve the red run. Eight tests failed for the intended missing behavior; the existing replay/global-RNG property passed. After repair, all nine pass.

**Why.** The red run demonstrates that the tests distinguish the pinned baseline from the repair. It also prevented a passing-after-the-fact suite from merely restating the implementation.

**Rejected alternative.** Editing frozen root fixtures or replacing baseline evidence was prohibited and would erase provenance.

**Probe/failure mode.** `checks/task-tests-red/` preserves the failing baseline run; `checks/task-tests/` is the final portable-runtime pass. The reusable workspace probe gives future reviewers a faster semantic/schedule regression than rerunning the full census.

## D8 — Keep audit targets read-only

**Choice.** Reproduce and document defects in `2e5d92febde0` and `113d9bb402d3` without changing their files.

**Why.** They are adversarial audit targets, not the assigned repair target. Mixing fixes would violate scope and make intake ambiguous.

**Evidence.** `AUDIT.md` and `checks/audit/*`. The first target has a repeated-color counterexample; the second has a production-materialized four-demo ambiguity. Recommendations are intentionally unimplemented here.

## Native parametric handoff — review-21a098f47523bb13 (2026-10-25)

A task-local native family now lives in `workspace/parametric/` without changing
production `generator.py` or the selected canonical authority.  The default
`control_selector=last_isolated` returns the canonical Racket program byte for
byte.  The alternate `control_selector=nearest_object` first measures the
remaining object's bounding box, selects the uniquely nearest isolated 1..4
control, carries that input-derived position/code as an intermediate, and then
uses the code to rotate the tightly cropped object.  The input plan is shared
across settings, deterministic, prefix-stable for 2–6 demonstrations and 1–4
queries, and stores four distinct queries including a substantive 30×30 scene.

The minimum two demonstrations reject the declared first/last, code-rank, and
fixed-code rivals.  A 64-seed finite audit covered 384 setting/count lessons
with no surviving harmful declared rival; this is finite evidence rather than a
universal uniqueness proof.  Native qualification passed at 2, 3, and 6 demos
for both settings and seeds 0/17, totaling 136 protected-Racket evaluations.
Sixteen one-query public projections passed saved-byte and leakage checks.  The
source-bound protected counterfactual substitutes the canonical last control
for the geometry-selected control and changes 36 output cells.

Retained evidence is under `checks/0e4adc584fa1/`; the current source inventory
is `workspace/parametric/evidence/manifest.json`.  The result is reviewer-ready
only.  Exact-byte owner integration, fresh native acceptance, and any training
admission remain separate decisions.
