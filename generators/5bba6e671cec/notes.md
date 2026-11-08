# Working notes: 5bba6e671cec

## Current review, 2026-10-22 — version 3.2.0

Source: `d56c7eaebcf43e35c8591cec7a204bc780c18ce6fc3eacbff24e525f7165edae`. Selected Racket `f90a485d851e` is unchanged in this review. The inherited 3.1.0 source was `73ec01f2d90b2accfdf4731c09f43998dd6a03d127398f117ea7e4d0b1d868b0`.

A newly tested first-cell-angle rival fits all eight canonical records/four unique inputs, but easy seed 0, indices 1–4, was a wrong-query lesson: the first three labels agree and the last differs. The retained counterexample contains the exact before lesson, Racket/rival outputs and two current refuters. Add `first_cell_angle` to the live registries and copy the bottom-region color to (0,1) in the quadrant profile so every four-profile cycle has redundant centroid evidence. This keeps the frame and two public axes intact. Reject negative sample indices and expose the existing period through `LESSON_SCHEDULE_PERIOD`.

Final measured checks: strict battery 12/12; task tests 34 plus 4,987 subtests; Racket production census 300 lessons/1,200 holdouts/656 unique inputs, zero ambiguity; period-4 seed-0 census 12 lessons/48 holdouts/21 unique inputs, zero ambiguity. The task-local Python diagnostic covers 720 overlapping lessons/2,880 holdouts/588 unique inputs and eight live rivals, with no ambiguity; it is not the Racket label authority. Exact public override probing passed 4,608 cases. Default lessons are three demos plus one query; forced overrides are outside the default teaching guarantee.

The direction/steps prototype in `workspace/parametric/` chooses a rule once per episode and exposes reusable audit/rescore tools. Four settings, 144 episodes/576 holdouts and 860 distinct Racket setting/input checks passed; canonical cw1 is byte-identical to the original program. The public projection withholds settings and query labels. This is a proposed extension with no training admission.

All evidence is finite. The four 8×8 frame templates remain narrow; bounding-box-center and largest-component-centroid alternatives agree on the bounded default support inspected. No universal induction or size-generalization claim is made. The new generator requires maintainer acceptance; historical approval is not transferred by editing evidence records.

## Historical notes (prior review, retained for provenance)

The following describes the earlier 2.1.0 → 3.1.0 repair and its then-current source, tests and authority synchronization. Its counts are historical, not final-source results for this review.

## 2026-10-04 repair

The imported 2.1.0 generator was not a canonical-distribution sampler. It emitted 11–15 cell zero-background grids containing four tiny compass pairs, excluded colors 4 and 7, had no pinned rule hash, and rejected every canonical example in `self_check`. The selected Racket behavior itself was correct; only two solution-record `target_code` fields were textually synchronized to the canonical program, with archival `raw_code` left unchanged.

Version 3.1.0 now emits 8×8 color-4/color-7 frame structures with two to four large whole-color regions. Public controls are reduced to two exact observable axes: `region_count` and `include_zero`. The diagnostic Python oracle, validator, executable semantic rivals, witnesses, and four-profile schedule are all source-bound to this task.

An intermediate three-profile curriculum passed the normal 12-stage battery and had zero ambiguity in default query placement, but the production lesson census found 398 ambiguous cases among 1,200 query rotations. The final four-profile schedule adds redundant row-order/quadrant/zero counterexamples so removing any one pair cannot erase all evidence against a declared rival.

Final evidence on generator SHA-256 `73ec01f2d90b2accfdf4731c09f43998dd6a03d127398f117ea7e4d0b1d868b0`:

- 12/12 final battery stages green.
- 19 task-local tests green, with 4,013 subtests.
- Production census: 300 lessons, 1,200 pairs, 1,200 query rotations, 0 ambiguities, 664 unique inputs.
- Exhaustive task-local probe: 720 cyclic lessons, 2,880 query rotations, 7 declared rivals, 0 ambiguities/errors, 588 unique inputs.

The finite rival registry is evidence against named shortcuts, not a proof of universal induction. Production labels remain Racket-authoritative; the Python oracle and workspace probe are diagnostics.
## Current reviewer considerations

Source SHA-256: `d56c7eaebcf43e35c8591cec7a204bc780c18ce6fc3eacbff24e525f7165edae`.

# Decisions for review-f47d4f2711392be5

## R1 — Add the missing rival and redundant evidence

The first-cell-angle rival fits every canonical record and an actual three-demo lesson, then fails the generated query. That establishes a teaching defect even though the previous battery passed its old finite rival set. Add the rival to the canonical/semantic/lesson declarations so future generic tooling sees it. Preserve the old failing lesson, then add one pixel to the quadrant profile to make it a second centroid witness. An unmutated finite geometry search did not produce the required simultaneous refuters; the retained mutation search selected the small change. See `checks/canonical-inspection/geometry-candidates.json`, `mutation-candidates.json`, and task `counterexamples/first_cell_angle.json`.

Keep the established four-slot schedule and all public controls. Production assembly is three demonstrations followed by one query from four consecutive unforced default indices. Every single-pair holdout is required to pass against the eight declared rivals. The period-4 fixed-seed census exhausts starts 0–3 at seed 0 across all three bands; it does not exhaust all seeds. The 300-lesson production census samples a wider source-bound population; the 720-lesson local Python probe adds overlapping cyclic windows. Forced per-pair overrides can defeat this lesson curriculum and are not covered by the default teaching claim.

## R2 and R3 — Enforce the input contract and expose the period

Reject negative `sample_index` consistently in both generation and schedule lookup; it is an index, not a signed random seed. Retain valid signed integer seeds and existing strict type rejection. Declare `LESSON_SCHEDULE_PERIOD = SCHEDULE_PERIOD` so the public exhaustive scheduler can inspect the existing four-period contract. This changes no scheduling algorithm. The first shared enumeration failed visibly on the missing declaration and is retained.

Bump version 3.1.0 to 3.2.0 because a geometry mutation changes deterministic emitted bytes. Reports, the fresh exposed solve and after checks all bind to source `d56c7eaebcf43e35c8591cec7a204bc780c18ce6fc3eacbff24e525f7165edae`. Version-specific reseeding means old/new seed grids need not have the same palette; exact before and after witnesses are both saved.

## Preserve canonical authority and constrain distribution change

The selected Racket rule already implements the intended whole-color centroid law. Preserve it, fixed colors 4 and 7, global treatment of zero/disconnected regions, 8×8 grids, the four frame templates and exact `region_count`/`include_zero` axes. Do not promote the diagnostic Python mirror to label authority. All production/census labels and the parametric evidence use Racket; local probes explicitly identify their diagnostic Python labels.

Larger grids and arbitrary frame topology could broaden the task but need a separate domain/curriculum study. This repair addresses an observed counterexample without inventing such a new distribution. Bounding-box-center and largest-component-centroid rivals remain indistinguishable on the bounded support inspected; this is an explicit coverage limitation, not a proven wrong-query lesson. No claim of universal identifiability is made.

The earlier repair synchronized selected target text while preserving divergent archival raw code. Those inherited bytes are untouched here. Do not rewrite authority or approval records to make the new source look approved; final approval belongs to maintainer intake.

## P1 — Parameterize the transformation once per episode

`PARAMETRIC-RULES.md` is suitable for a bounded direction/step extension. Four settings preserve the same visual entities and input domain while changing the target transformation. Choose one SHA-256-derived setting from the episode seed before generating any pair, and use its exact Racket program for every label. The canonical default must equal canonical program bytes. Do not sample a new rule for each example or reveal setting/query labels in public challenges.

Two-region and other modulo aliases prevent some individual inputs from distinguishing every setting. Score full mixed-region lessons and distinguish `survived_all` from an ambiguous differing query. All four holdouts are measured separately from ordered production. Require pairwise cross-setting witnesses, but do not mistake these witnesses for a universal lesson guarantee.

Build the reusable authoring/replay tool in the task's allowed `workspace/parametric/` directory. It validates source/asset inventories, exact programs, seed choices, regenerated inputs, live registry adapters, Racket labels and public projection. Keep the manifest/private labels out of solver-visible data. The extension remains proposed; promotion to shared tooling or training needs a separate maintainer decision. The 11 focused tests include malformed inputs, parameter handling and meaningful evidence-tampering failures; the exact current audit/replay is `checks/parametric/final-current/`.

## A1 and A2 — Audit without unauthorized peer changes

For `d3ae93aa8d37`, use the production generator and then a separate supported Racket application to establish an actual differing query, rather than repeating the inherited all-agree lesson. For `f35919cb93b9`, distinguish failed API promises and metadata bypass from ordinary default quality. Test the docstring's crash assertion: the missing-pivot reference application actually returns an unchanged grid. Report that evidence, not the comment. Both peers stay unchanged, with exact source-bound findings in `AUDIT.md`.

## Evidence and stopping rule

Keep genuine failures, before results, counterexamples and both real solve records. Superseded successful parametric outputs may be compacted with their manifests/logs while the complete final-current audit remains retained. Do not fabricate a failed solve; both one-attempt records pass visible examples and leave hidden-query correctness unknown. Finish only after the final source passes the strict battery, required-rotation censuses, task tests, parametric replay, visible-only solve, and fresh return patch/test replay. Do not broaden to the full repository suite without a concrete unresolved risk.
