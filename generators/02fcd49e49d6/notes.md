# Working notes: 02fcd49e49d6

## 2026-10-26 parametric build

- Preserved the imported `generator.py` and exact canonical Racket program. The canonical setting is `selection=all_pairs`.
- Added a matched-input alternative, `selection=cue_gap`. Step A finds the unique row whose two 8 endpoints surround a color-1 midpoint and derives that row's even endpoint gap. The intermediate is that gap. Step B paints red only empty midpoints of two-8 rows with the derived gap.
- The scene grammar includes matching and nonmatching gaps, an odd-distance row, an occupied-midpoint row, and a unique cue. The four-query profile reaches a substantive 30×30 case with boundary-spanning examples. Inputs are identical across settings for a given seed/demo/query configuration.
- Repaired inherited nonportable test paths with `reviewer_support.find_root`, `canonical_pairs`, and `load_selected_generator`; generator behavior did not change.

## 2026-10-26 second-round adversarial repair

- Protected replay of the first-round lesson exposed a cue-ignoring modal-gap hypothesis that fit both demonstrations and disagreed on a query. A broader scan then found fixed two-result caps, minimum/maximum-gap rules, and cue-relative top/bottom/nearest/farthest rules on subsets of seeds.
- Rebuilt the teaching schedule so the cue gap is never an extreme, its positive count cycles through 2/3/4, a non-cue modal decoy occurs one more time, a non-cue rare gap occurs once, and positional guard rows carry non-cue gaps.
- Promoted those failures into a reusable 25-rule `rival_outputs` catalog and a compact 5,000-seed census in `workspace/parametric/probe.py`; future agents can extend the catalog without storing bulky episodes.
- The first-round ambiguity is retained as protected-Racket evidence under `checks/round2-ambiguities/02f-two-demo-modal-{candidate,certificate}.json`.

## Verification and evidence

- Focused task suite: 22 tests plus 11 subtests; packet-native JUnit receipt reports 33 passed cases, 0 failures, 0 errors.
- Coverage audit: 20 Python cases over both settings, seeds 0/17, 2–6 demonstrations, and four queries.
- Adversarial census: 5,000 seeds × 2 settings, 10,000 minimum-demo cases, 25 named rivals, 500,000 shortcut evaluations, no unexpected survivor.
- Protected Racket: four probe jobs and the authoring preflight each performed 32 label evaluations. Preflight passed with 4 jobs, 2 settings, 24 parametric labelled pairs, and 3 canonical pairs.
- Causal witness: the selected query derives cue gap 6; replacing it with gap 4 changes the protected-Racket final output on the same input (`wrong_intermediate`).
- Inventory: `workspace/parametric/evidence/manifest.json`; qualification: `checks/02fcd49e49d6/qualification/qualification.json`; witness: `checks/02fcd49e49d6/causal/witness.json`; final probe: `checks/final-02fcd49e49d6-probe/report.json`; final task tests: `checks/final-02fcd49e49d6-tests/result.json`.

## Limits

This is a source-bound authoring prototype. The finite seed/rival census does not prove universal uniqueness. Owner source review, native qualification/acceptance, and training admission were not performed.
