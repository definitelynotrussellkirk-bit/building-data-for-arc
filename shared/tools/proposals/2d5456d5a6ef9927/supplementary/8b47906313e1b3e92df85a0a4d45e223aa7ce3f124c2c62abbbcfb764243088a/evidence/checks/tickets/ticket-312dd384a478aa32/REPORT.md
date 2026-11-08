# Allocation-quality ticket `ticket-312dd384a478aa32`

**Outcome: completed one source-bound three-record assessment and one canonical-Racket probe.** No generator, approval, catalog weight, draw probability, or training artifact was changed. The proposal below is a bounded owner-time experiment, not a production allocation decision.

## Deterministic sample and current allocation context

The ticket pins `71d5c4ac6ea3`. Applying `random.Random(int(ticket_seed, 16)).sample(...)` to the sorted current generator records, after excluding the official main target, audit target, and primary, selected `75837d4fa905` and `90082143f2ec`. The eligible peer count was 297. Exact selection logic and IDs are in `comparison_selection.json`.

The packet contains 300 current generator records from an owner catalog of 3,941 and a 154-record main authoring pool. All three sampled catalog weights are `1.0`, but those equal numbers do not imply equal realized allocation: `71d5c4ac6ea3` is unapproved, coverage-only, and outside the main pool; `75837d4fa905` is approved but coverage-only; `90082143f2ec` is approved and selected as an unfinished approved original. Approval filtering and focus-pool membership therefore dominate the nominal equal weights.

The dated catalog rows are not current source contracts for this sample. Their versions are `2.0.0`, while current source versions are `2.0.1`, `3.0.0`, and `4.0.0`; the catalog axis lists also disagree with all three current sources. `inspection.json` keeps both views and treats the current source/hash plus review index as authoritative for this assessment.

| Record | Current source-bound evidence | Representation, teachability, and cost assessment |
|---|---|---|
| `71d5c4ac6ea3` (`bank:1f065edbcf08`) | Source SHA `e70ca9…` and rule `ed3afc80127d` match the ticket. Unapproved; no task-local tests, rule pin, exact override observer, named rivals, lesson checker, schedule contract, or parametric workspace. Two reviewer-reported audits are retained; one reproduces a lesson-level fixed-origin shortcut. | Small 9×10 to roughly 11×12 ordinary grids make label/token cost low, but current lesson quality is blocked: random per-input anchor movement does not guarantee that demonstrations teach anchor-relative offsets. Nine advertised controls include singleton/alias axes, and four-query support is unqualified. Repair has high expected value because the defect and witness are specific, but generating volume before repair has poor quality per cost. |
| `75837d4fa905` (`bank:ece0cc5101a3`) | Source SHA `e27e05…`, rule `e56cca9b3b6c`, approved. Current v3 source exposes exactly three observable axes, pins the rule, has focused tests, named semantic rivals, lesson-identifiability checks, retained witnesses, and a reviewer-reported 300-lesson/1,200-rotation clean census. No parametric workspace yet. | Two-to-four distinct 2×2 squares on 7–16 by 8–18 grids. Boundary clipping and a canonical-fitting interior-only shortcut are executable. This is the strongest near-term four-query candidate in the sample: compact scenes, explicit grammar, constructive generation, and low review risk. Remaining cost is chiefly episode export/deduplication rather than semantic repair. |
| `90082143f2ec` (`training:e26a3af2`) | Source SHA `161d76…`, rule `a86d1f36d1d2`, approved and in the main pool. Current v4 source has five exact axes, an eight-slot counterbalanced schedule, tests, named rivals, retained shortcut witness, and reviewer-reported exhaustive schedule plus 300-lesson/1,200-rotation checks. No parametric workspace yet. | Rich 13–15 by 14–17 nine-color noisy-band scenes with 3–5 bands. Teachability is strong after the shape/orientation repair, but each label carries about 182–255 input cells, materially more context than the other sampled records. This supports some allocation for diversity, but not equal volume absent measured model benefit per token. |

No ARC-GEN or RE-ARC record was selected by this seed sample. The assessment therefore makes no quality or volume ranking for those sources; provenance alone would not have been accepted as a quality signal. `TRAINING-CONTEXT.md` is used only as its dated October 23, 2026 snapshot, not as proof of the refreshed packet distribution. No model-loss or mastery run was performed, and high loss is not treated as a defect.

## One executed probe

From the extraction root:

```text
python3 review.py run python3 -B ../checks/tickets/ticket-312dd384a478aa32/allocation_probe.py
```

The probe directly loaded the pinned production source and unchanged canonical Racket rule, then generated seed `2`, difficulty `easy`, samples `49..55`: three demonstrations and four distinct queries. All seven 9×10 inputs passed the current `self_check`; all seven canonical Racket outputs matched an independent Python mirror. Racket startup plus execution completed in 2.944 seconds, with 0.010 seconds spent labeling after startup.

The three demonstration anchors were all `(2,3)`. A plausible rival ignored the actual color-9 anchor and always computed color-1 offsets from `(2,3)`. It matched all three authoritative demonstration outputs. Query anchors were `(3,2)`, `(2,1)`, `(3,2)`, and `(1,2)`; the rival disagreed with the authoritative query outputs in **8, 8, 6, and 6 cells**. Query answers were not used to select or eliminate the rival.

This reproduces the retained source-bound defect while extending it to the requested four-query shape. It does not estimate corpus frequency. The exact episode, private answers, visible-content-named public challenge, Racket runtime identity, source/rule hashes, and per-query differences are in `probe_result.json` and `private_episode.json`.

## Alternative owner allocation and bounded stopping rule

For a future **60-minute owner budget across only these three sampled records**, compare equal `20/20/20` minutes with a proposed **`30/20/10` split**:

- **30 minutes — `71d5c4ac6ea3` repair, no volume generation.** Add the canonical rule pin, honest/rejecting controls, a named fixed-origin competitor, and a deterministic schedule or lesson qualification that makes every three-demonstration lesson contain more than one anchor origin. Add focused source-bound tests and a Racket witness. Stop immediately if the current rule pin or mirror parity fails. Do not admit episodes while any fixed-origin rival survives all demonstrations.
- **20 minutes — `75837d4fa905` four-query export pilot.** Build the missing parametric episode wrapper around the current source rather than changing the canonical generator. Require three demonstrations, four distinct queries, demonstration-only elimination of declared rivals, sorted content-addressed public output, and duplicate rejection before writes.
- **10 minutes — `90082143f2ec` four-query/cost pilot.** Exercise the existing eight-slot schedule and measure accepted queries per input cell and per Racket second. Keep the source unchanged unless the pilot exposes a source-bound failure. Its larger contexts justify lower initial volume until training benefit per token is measured.

This split is an estimate: it favors one precise blocker repair and one mature low-cost exporter over equal time on a mature but larger-context family. It does **not** claim a globally optimal mix.

A bounded follow-up pilot should run only after the primary repair gate passes:

1. Materialize at most four accepted episodes for each approved/repaired family, with at most eight attempts per family. Each episode has three demonstrations and four queries.
2. For the two currently approved records this is 56 accepted Racket labels, with a hard 112-label attempt ceiling. A repaired primary may add 28 accepted labels under the same cap.
3. Require exact source/rule identity, valid current controls, seven distinct inputs, four queries distinct from demonstrations, authoritative Racket labels, zero public-payload collisions, and demonstration-only rejection of named relevant rivals.
4. Stop a family immediately on source drift, Python/Racket disagreement, malformed public/private separation, or a surviving named rival. Stop expansion when more than four of eight attempts fail validation, distinctness, deduplication, or teaching checks.
5. Compare accepted supervised queries per 1,000 input cells, Racket seconds per accepted episode, public-ID uniqueness, and rejection reasons. Do not change global weights from this pilot alone; require a separate model-learning comparison.

## Limits

This is one seeded three-record sample and one executed episode on the primary. Historical censuses in review notes remain reviewer-reported and were not rerun. Catalog freshness mismatches mean catalog reach/axis summaries are descriptive history, not current contract proof. Proposed parametric wrappers are separate from production capability and training admission.
