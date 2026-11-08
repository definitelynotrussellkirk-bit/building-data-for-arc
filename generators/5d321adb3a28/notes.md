# Working notes: 5d321adb3a28

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5ba20f935adf01ed25f58b70211cdd0c945979dadc1f1106b693816d5dae0c15`.

# Design decisions for `5d321adb3a28`

Final generator: `v3.2.2`, SHA-256 `5ba20f935adf01ed25f58b70211cdd0c945979dadc1f1106b693816d5dae0c15`.

## D1: treat the retained six-relation grammar as the baseline, not as proof of complete canonical coverage

**Prior rationale.** Retained note `GNOTE-003386` explains that the compact grammar pairs adjacent endpoints to teach one positive relation per orientation plus mismatch and long-gap controls while keeping object counts near canonical support. That rationale was sound for shortcut refutation, and the baseline battery was fully green.

**New evidence.** `checks/target-count-before.json` showed that all four canonical pairs contain three positive gaps while every one of 300 baseline samples contained two. The prior grammar covered the *types* of relation but not their canonical multiplicity.

**Decision.** Preserve all six prior semantic obligations and add a seventh relation: a second target in one orientation. This is a targeted distribution repair, not a rewrite of the rule or curriculum.

## D2: sample target multiplicity internally, not through a new public axis

**Chosen design.** Each draw deterministically samples one of two internal profiles, `2h1v` or `1h2v`, from the task/version/seed/sample-index RNG. The public API remains exactly the inherited `scene_profile` and `target_relation` axes.

**Rejected alternative.** A public `target_count_profile` override was implemented first. Its regression passed in isolation but the frozen fixture correctly failed because it asserts the exact inherited two-axis surface. The attempted patch and rationale are retained at:

- `repo/generators/5d321adb3a28/workspace/rejected-public-target-count-axis.patch`
- `repo/generators/5d321adb3a28/workspace/rejected-public-target-count-axis.md`

**Reason.** Target multiplicity is a curriculum balancing detail, not a meaningful user-facing combinatorial control. Making it public would expand the compatibility contract without improving task semantics.

**Failure mode.** An internal profile can drift silently. The new task tests and `probe_target_count.py` make both profile support and exact change counts observable.

## D3: require exactly three ordinary-draw changes and teach against a two-change cap

**Chosen design.** Generated-form validation accepts only signatures with three targets in a `2:1` orientation split plus exactly one mismatch and one long-gap control per orientation. `canonical_target_multiplicity` is an executable witness, and `two_change_cap` is an executable competitor.

**Alternatives considered.**

1. Merely increase the number of positive motifs without adding a rival: rejected because the teaching obligation would remain comment-only.
2. Randomize between two and three targets: rejected because it would retain substantial off-support mass even though all usable canonical pairs agree on three.
3. Generate four or more targets: rejected as unsupported by the observed canonical demonstrations and unnecessary for the identified defect.

**Measured result.** At the final SHA, all 300 probe draws change exactly three cells, with both orientation profiles represented in every band.

## D4: preserve canonical-scale component support with deterministic color separation

**Initial failure.** Duplicating an orientation with the same color made all sampled generated components top out at size 3. The intermediate battery failed defect lint at SHA `99f2bce07165c719b095a4d7ed616fd9679441b7ae59d65da5950778d1ce0c8e` (`checks/after/`).

**Chosen repair.** Sample `separate_control_lead`; when true, use a distinct color for the mismatch-control lead. This separates a compact cluster without changing the target, mismatch, or long-gap semantics.

**Why not force all endpoints isolated.** That would return to the old 10–14-object problem the compact grammar was designed to avoid. The final branch keeps samples compact while reaching canonical-scale components.

**Failure mode.** Color changes can accidentally create unintended local brackets. `_analyze_grid`, exact signature checks, ambiguous/uncovered-cell checks, and `self_check` guard this on every accepted draw.

## D5: distinguish canonical shortcuts from generated-lesson competitors

**Problem.** `CANONICAL_SHORTCUTS` inherited every semantic rival, including `horizontal_only` and `vertical_only`, although canonical examples contain both orientations and refute those rules.

**Chosen design.** Keep all five rules in `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`, but declare only `ignore_endpoint_equality` and `fill_arbitrary_distance_spans` as canonical shortcuts. A task-local regression now verifies every declared shortcut against every canonical pair.

**Reason.** The collections answer different questions:

- canonical shortcuts: wrong rules indistinguishable from the intended rule on all usable canonical demonstrations;
- lesson competitors: wrong rules each generated lesson must refute, whether or not they survive canonical data.

**Failure mode.** A future rival can be placed in the wrong collection. The new canonical-fit regression and lesson census make this a hard failure/evidence item.

## D6: do not change Racket authority

The selected rule already matches all canonical pairs and expresses the intended local operation. The defect was entirely in input distribution and metadata. Changing Racket would have expanded scope without addressing the measured problem.

Final authority evidence shows selected canonical/target sources synchronized at `980e1ed5540b`, and the pre-existing archival source remains execution-equivalent. See `checks/after-final-v322-complete/checks/5d321adb3a28_after_authority_sync.json`.

## D7: retain reusable probes and failed experiments

Two task-local tools were added:

- `workspace/probe_target_count.py`: compares canonical and generated change-count/orientation/object/shape histograms using the actual generator and canonical ledger.
- `workspace/make_shortcut_witness.py`: constructs a deterministic generated witness for the strongest canonical-fitting rival, records exact differing cells, and emits inputs/outputs for supported Racket verification.

The rejected public-axis patch and the failed intermediate battery are retained. They are useful evidence for future agents and prevent repeating the same design detour.

## D8: stopping rule

Stop after all of the following held on the same source bytes:

- final battery 12/12 green;
- 10/10 selected task tests green;
- 300-lesson census materialized with zero ambiguity and every declared rival refuted in every lesson;
- canonical shortcut declarations fit 4/4 canonical pairs;
- exact patch applies to a clean original packet and focused tests pass there;
- final post-repair solve is bound to the final generator hash.

All conditions are met. Remaining limitations are finite grammar/support and finite named-rival coverage, not known blockers.
