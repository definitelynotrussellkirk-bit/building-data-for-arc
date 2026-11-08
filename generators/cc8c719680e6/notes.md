# Working notes: cc8c719680e6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 — review-218b8270de3d601b, v2.2.0

Reproduced two natural lessons accepted by v2.1.0 although an undeclared
connectivity rival fit every demonstration and failed the Racket-labeled query.
The baseline same-color 8-connected rival survived 2,983/3,000 direct four-demo
windows; color-blind 4-connectivity survived 2,434/3,000. Contacts were possible
but rare, correcting the initial source-only zero-support hypothesis.

Generalized n>=3 scenes now construct diagonal-only same-color and orthogonal
different-color contacts, with D4/translation variation and a free fourth
satellite. Both rivals and their witnesses are declared. The four-cycle canonical
slots, exact axes and Racket rule 8f9e53b42241 are retained. The lesson hook now
returns validation findings before rival scoring and accepts semantically
sufficient lessons without imposing schedule-wide size/count/palette quotas.

The final 3,000-window matched census has no surviving declared rivals. A separate
production census covers 300 Racket-labeled lessons with no ambiguity or warnings.
All 1,296 joint override checks pass; all 50 portable test executions pass
(30 distinct cases, 20 legacy repeats). Detailed evidence and exact source hashes
are retained in this review's return and the workspace reports.

Known limits: generalized three-component scenes have a 5x5 contact core; small
component morphologies and the previous canonical-profile support remain bounded.
Unique output counts fell about 6–7% per band in the matched sample. Arbitrary
query rotations can remove the sole repeated-color witness: 27/180 tested
rotations remain genuinely ambiguous and are correctly rejected. These are
explicit follow-up targets, not claims of universal induction or model accuracy.

## 2026-10-04 review repair

Baseline generator SHA-256: `fcb5e074619f09fc2cdbac112de79105426765a444efe592284d15f071d52a78` (`VERSION = 2.1.0`).
Final generator SHA-256: `4eb641330e52b43504f9d837a50699987e5b7fc18d93b20926b9f7ea2674fda7` (`VERSION = 2.2.0`).
Canonical rule hash remains `8f9e53b42241`; no Racket authority was edited.

The retained prior audits were useful leads for canonical parity, overrides, and named-rival coverage, but they did not measure the component-shape vocabulary independently. A returned-grid-only probe over 250 seeds × 4 sample indices in each difficulty band found that the selected baseline exposed only 13 normalized shapes and exactly four bbox spans (`2x2`, `3x2`, `3x3`, `3x4`). Every one of eight sampled four-example windows per band therefore fit a legacy-span lookup rival. The baseline also reached only two of the three canonical joint morphology profiles.

The repair keeps the canonical-linked schedule and all public axes, but uses D4 variants of connected generalized shapes in wide/tall scenes. It adds spans `2x3`, `3x5`, `4x3`, `4x4`, and `5x3`, and samples both lawful 9×9 canonical morphology multisets. Region-based anchors keep component bbox footprints separated and preserve `edge_mode` observability.

Regression tests were written first. On the baseline they failed with 8 failures / 40 passes in the portable duplicated test layout: the third canonical joint profile was unreachable and every tested lesson window used only legacy spans. The repaired source passes 50/50 focused tests, the 12-stage final after battery, and a source-bound census of 100 lessons per band. That census refuted the executable `legacy_bbox_span_lookup` rival in all 300 lessons.


The first draft of the workspace probe accidentally called producer-owned `_components`, `_analyze`, `_morphology_signature`, and `rule_mirror` helpers. A generate-only proxy regression caught this during final self-review. Probe v2 now calls only `generate` and locally reconstructs connected components, official bbox-outline outputs, and canonical joint profiles from the portable canonical ledger; the before/after counts were remeasured unchanged.

Independent post-repair morphology measurement found 42 normalized shapes per band, all three canonical joint profiles, five novel spans, and zero of eight sampled windows per band lacking a novel span. The finite bank and quadrant-separated generalized placement remain deliberate domain limits; these checks refute declared and measured shortcuts but do not prove universal identifiability.

Reusable evidence:

- `workspace/morphology_distribution_probe.py`
- `checks/morphology-distribution-before.json`
- `checks/morphology-distribution-after.json`
- `checks/final-evidence-summary.json`
- `checks/lesson-census.json`

## 2026-10-03 — maintainer combination, v2.3.0

Two independent v2.2.0 repairs overlapped: review-218b8270de3d601b added connectivity counterexamples, while review-27512c2efdb6959e broadened morphology and canonical profile support. Neither parent test report establishes this combination's outcome. The new version keeps contact layouts for repeated-color three/four-component scenes and diversified quadrant layouts for distinct-color wide/tall scenes. Each default four-demo window therefore includes both kinds of evidence. Both rival sets and both workspace probes are retained. Targeted source-bound checks are recorded in the integration receipt; no full battery or private solve was rerun.

Historical morphology counts and arbitrary-query rotation ambiguities above remain tied to their parent sources; they are not measurements of v2.3.0. The merged curriculum is still a finite shape vocabulary, and arbitrary query rotations may remove a sole distinguishing witness.
## Current reviewer considerations

Source SHA-256: `5f8ab6d1ea311ab8de97d061a6063bf6cc4d7fc788aaab43006a7a6a5f405928`.

# Decisions for `cc8c719680e6`

## D1 — Treat narrow morphology support as the repair target

**Observed baseline.** The generator already passed its full battery and focused semantic suite. An independent returned-grid census nevertheless found only 13 normalized shapes and four bbox spans in each band, with the 2×2 L occurring 1,250 times among 2,750 components per band. All 24 measured four-example windows used only the same four spans.

**Decision.** Repair the input distribution rather than the rule. The canonical operation was correct; the failure was that a finite span/template lookup could masquerade as the rule on production lessons.

**Alternatives rejected.** Adding more random positions or colors would raise exact-grid uniqueness but would not break the morphology lookup. Merely declaring a new rival without changing sampling would make the strict semantic gate fail but would not improve data. Rewriting the Racket rule was unnecessary and would create authority churn.

**Probe.** `workspace/morphology_distribution_probe.py` independently reconstructs components and support from returned grids. Before/after reports are under `checks/morphology-distribution-*.json`.

## D2 — Expand connected morphology with D4 variants, not arbitrary noise

**Decision.** Build a finite bank from lawful connected base shapes and their rotations/reflections. Wide and tall profiles now include spans `2x3`, `3x5`, `4x3`, `4x4`, and `5x3` in addition to the legacy spans. At least the primary generalized component has a source cell strictly inside its bbox, preserving the fresh-canvas deletion witness.

**Why.** D4 expansion gives many semantic-equivalent forms without introducing disconnected “components,” diagonal-only joins, or arbitrary pixels. The resulting output still teaches exactly one operation: replace each 4-connected component with its own bbox border.

**Alternatives rejected.** Free random walks were considered but would need more validation for self-touching, accidental holes, and excessively dense boxes. Arbitrary polyomino enumeration would add complexity without evidence that more than the measured 42 normalized forms is currently needed.

**Failure modes and limits.** The bank remains finite, so an even larger support-table rival is possible in principle. The new shared-tool proposal in `FEEDBACK_TO_CODEX.md` therefore recommends generic support-compression checks rather than relying only on this task-local rival.

## D3 — Use separated scene regions for generalized placement

**Decision.** Place generalized components in nonoverlapping quadrant-like regions with a one-cell separator and draw border or interior anchors inside those regions.

**Why.** The task's selected domain rejects overlapping component bbox footprints. Region placement makes that invariant constructive, keeps per-component colors unambiguous, and preserves the observable `edge_mode` axis.

**Alternatives rejected.** Global rejection sampling would be simpler locally but could become seed-sensitive, slow, or biased as larger shapes are added. Allowing bbox overlap would widen the oracle domain beyond the selected generator contract and could make one component's output overwrite another.

**Limit.** Generalized scenes retain a coarse spatial partition. This is documented rather than hidden; future work could add a collision-free global placer and compare occupancy distributions before replacing it.

## D4 — Reach both 9×9 canonical morphology multisets

**Observed gap.** The baseline strict sampler reached the 7×7 canonical profile and only one of the two 9×9 morphology signatures, although all canonical inputs passed validation.

**Decision.** In the `canonical_9` profile, deterministically keyed randomness chooses between the training and held-out 9×9 morphology multisets. The schedule, dimensions, edge mode, and component count are unchanged.

**Why.** Canonical acceptance alone is weaker than production support. Sampling both lawful signatures prevents the canonical-profile portion of the data from silently omitting a real canonical branch.

**Test.** Across 64 seeds at canonical schedule positions, the observed exact joint-profile set must equal `_CANONICAL_JOINT_PROFILES`.

## D5 — Preserve the old shortcut as an executable rival

**Decision.** Add `_legacy_bbox_span_lookup`: it applies the correct bbox transform only to the four former spans and preserves unseen shapes on the fresh output canvas. Pair it with the `component_bbox_spans_generalize` witness.

**Why.** The defect should remain executable and source-bound. A prose warning can regress silently; a rival can be tested in focused lessons and by the shared lesson census.

**Alternative rejected.** A rival keyed to exact normalized shapes would be stronger but much larger and more coupled to implementation details. The span rival captures the simplest reproducible shortcut that fit the measured baseline and fails immediately on the repaired support.

## D6 — Keep exact axes and rule authority unchanged

The version was bumped from 2.1.0 to 2.2.0 because output distribution changes invalidate keyed generation caches. No axis was renamed or added. The override battery accepted all 8,280 legal draws and rejected an unknown key. No Racket source, canonical row, or base authority file was changed; rule hash remains `8f9e53b42241`.

## D7 — Adjust the deletion regression from a fixed slot to a lesson invariant

One newly sampled exact 9×9 canonical training morphology contains no source cell strictly inside its bbox, so a test that required deletion at one fixed schedule position was over-specific. The semantic requirement is that a four-example lesson teach fresh-canvas deletion; the regression now requires at least one lesson member with a real deletion witness. The shared semantic gate and 300-lesson census confirm the declared rivals remain refuted.

## D8 — Retain conservative limits

No claim is made that 42 shapes or 300 lessons prove identifiability against every possible program. Exact-input uniqueness is not semantic diversity, declared-rival checks cover only declared rivals, and the census does not rotate every pair into the query position. These limits are carried in `checks/lesson-census.json` and the opening review brief.
