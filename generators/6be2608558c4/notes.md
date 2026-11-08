# Current notes: 6be2608558c4

## Intended rule

The nonzero cells in the top-left 5×5 window define a connected binary exemplar. Erase that window conceptually, find the unique 4-connected body component with the same normalized binary shape, crop it to its bounding box, and recolor its foreground cells 2. Color and absolute position are irrelevant; exact normalized shape is decisive.

The selected Racket authority was not changed. Current pin: `RULE_HASH=11381854d14b`.

## Current ordinary distribution (version 3.0.0)

- Grid dimensions are exactly controllable: height 11–12, width 13–15.
- Exemplar size is exactly controllable: 4–6 cells, connected, monochromatic, and contained in a 2×2 to 3×3 bounding box.
- There are exactly three separated monochromatic body components and four distinct nonzero input colors; output color 2 is absent from inputs.
- All three body components share the exemplar’s cell count and bounding-box dimensions, but their exact normalized shapes are distinct.
- Exactly one body shape equals the exemplar.
- The correct component rank cycles `0,1,2` by `sample_index`; three demonstrations are required.
- Easy chooses farther-shape decoys; hard chooses nearest-shape decoys. Exact axis domains remain global in every band.

## Reversed legacy decisions

Version 2.0.1 used random polyominoes, capped placement retries, 2–3 arbitrary body components, weak validation, and eight advertised axes including dead aliases/singletons and malformed textures. Those choices had no retained rationale beyond source comments. They were replaced because the old contract silently accepted typoed overrides, admitted malformed scenes, did not guarantee placements, and allowed coarse/position shortcuts.

Malformed modes now live in `mutation_fixtures()` rather than the public ordinary distribution. The public axis surface is reduced to `grid_h`, `grid_w`, and `exemplar_size`; unknown, badly typed, and out-of-range overrides fail loudly.

## Teaching contract and retained rivals

Declared competitors:

1. always choose the middle body component;
2. choose the first component with the exemplar’s cell-count/bbox signature;
3. choose the last component with that signature.

All five canonical pairs place the correct component at rank 1, so the first competitor is the strongest canonical shortcut. The exact generated disagreement is retained at `counterexamples/fixed-middle-shortcut.json`. `workspace/reference_probe.py` independently reconstructs the rule from pixels and exhausts sliding starts/query rotations.

## Evidence

- Final generator SHA-256: `8a1e61f04309cb16433e973b0b011d5469bee4effe9145493661bc72622e1669`.
- Final battery: all 12 stages green.
- Final focused suite: 25 tests passed.
- Large census: 300 lessons, 1,200 query rotations, 0 ambiguity, 1,200 unique inputs.
- Local probe: 270 sliding windows, 1,080 rotations, 292 unique inputs, balanced profiles, 0 issues.
- Post-repair exposed solve: revision 1 passed all 3 visible pairs; earlier rule exposure was declared.

## Known limits and open findings

- The ordinary sampler deliberately stays inside the canonical dimension/palette/morphology envelope; it does not claim the full mathematical execution domain of the Racket program.
- `self_check` validates authority/canonical support, not every stronger curriculum property: canonical decoys have heterogeneous signatures. Same-signature and three-distinct-shape guarantees are enforced by generation plus focused/probe tests (`checks/self-review-validator-boundary/report.json`).
- It always uses exactly three body candidates.
- Rival checks are finite evidence, not a proof against every possible induction.
- Training approval remains external to this review.
- No unresolved blocking finding remains for this selected generator.
## Current reviewer considerations

Source SHA-256: `8a1e61f04309cb16433e973b0b011d5469bee4effe9145493661bc72622e1669`.

# Decisions: 6be2608558c4

## D1 — Preserve the authority; repair only the input curriculum

**Prior choice:** version 2.0.1 described the intended exemplar-match rule but did not pin its authority. The original rationale is not recorded beyond source comments.

**Decision:** leave all Racket/canonical sources unchanged and pin `RULE_HASH=11381854d14b`.

**Alternatives considered:** rewrite the rule to resolve sampling ambiguity; broaden the rule domain. Both were rejected because the selected authority already matches all canonical pairs and the defects were in sampling, validation, and teaching.

**Probe/evidence:** rule smoke, Racket lint, and authority sync are green in `checks/after-attempt1/`.

**Failure mode/limit:** one archival copy differs, as reported by authority sync, but it is not the selected execution authority.

## D2 — Construct, rather than retry, the complete lesson geometry

**Prior choice:** random-walk polyominoes and capped placement loops produced 2–3 arbitrary distractors; placement return values could be ignored. The source comment suggests variety was the rationale, but no retained decision record exists.

**Decision:** enumerate connected 4–6-cell shapes inside 3×3, group them by `(cell count, bbox height, bbox width)`, select three distinct shapes from one group, and place them with guaranteed gaps.

**Alternatives considered:** keep rejection sampling with larger retry caps; use a small fixed motif bank. Retry caps retain hidden failure paths; a tiny fixed bank encourages memorization. Enumeration is finite, deterministic, and sufficiently diverse.

**Probe/evidence:** focused construction tests and `workspace/reference_probe.py`; no generation errors in the 600-draw semantic census or 1,080-pair local probe.

**Failure mode/limit:** the shape domain is intentionally bounded to 3×3 and 4–6 cells.

## D3 — Make coarse signatures maximally uninformative

**Prior choice:** distractors generally differed in size and bounding box, allowing cell-count/bbox shortcuts.

**Decision:** all three body candidates have exactly the exemplar’s cell count and bbox dimensions; only one has its exact normalized shape.

**Alternatives considered:** one same-signature decoy plus one arbitrary decoy; random signature collisions. Those leave lessons where a coarse rule succeeds or make the teaching guarantee probabilistic.

**Probe/evidence:** every draw checked by `workspace/reference_probe.py` has three distinct exact shapes with one common signature.

**Failure mode/limit:** a learner can assume three candidates because the ordinary curriculum always has three; this is documented rather than presented as a universal authority constraint.

## D4 — Cycle the target rank and require three demonstrations

**Prior choice:** all five canonical pairs place the target at body-component rank 1. The old generator randomized position but did not guarantee a complete anti-position lesson.

**Decision:** `schedule_profile = sample_index % 3`, `SCHEDULE_PROFILES=(0,1,2)`, and `EXAMPLES_NEEDED=3`.

**Alternatives considered:** random rank per pair; four or more demonstrations; canonical anchoring. Random ranks cannot guarantee coverage in a lesson, and more than three examples are unnecessary for the declared fixed-rank rivals.

**Probe/evidence:** every four-pair sliding window and all four query rotations pass in focused tests and the local 270-window probe; the large census passes 1,200 rotations.

**Failure mode/limit:** this establishes coverage for declared rivals, not every possible rule.

## D5 — Remove deceptive axes instead of making cosmetic use of them

**Prior choice:** `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` were advertised even when singleton, dead, aliases, or malformed modes.

**Decision:** expose only three exact, pixel-observable, globally supported axes: `grid_h`, `grid_w`, and `exemplar_size`. Reject unknown keys, booleans, coercible strings/floats, and out-of-range values.

**Alternatives considered:** preserve legacy names as aliases; declare many incompatibilities. Aliases would keep false independent controls, and incompatibility declarations would paper over a simple constructive domain.

**Probe/evidence:** final override stage passes with unknown-key rejection; boundary combinations pass in all bands.

**Failure mode/limit:** this is a deliberate public API break from deceptive legacy controls; version was raised to 3.0.0.

## D6 — Give difficulty a semantic role without narrowing overrides

**Intermediate choice:** the first repair ignored difficulty, producing byte-identical bands.

**Decision after reversal:** keep the same exact axis domain in every band, but choose farther-shape decoys for easy and nearest-shape decoys for hard. Medium/default samples decoys broadly.

**Reason:** defect lint correctly flagged dead bands. Color-only or position-only changes would silence the warning without altering reasoning difficulty.

**Probe/evidence:** `checks/task-tests-difficulty-red.log` fails before the change; the final difficulty test and defect lint pass.

**Failure mode/limit:** symmetric-difference distance is a local difficulty heuristic, not a calibrated human/model difficulty score.

## D7 — Define the ordinary domain with a strict, non-throwing validator

**Prior choice:** `self_check` accepted no-exemplar and most malformed scenes and checked little beyond nonzero presence.

**Decision:** require canonical envelope dimensions, integer ARC colors, no input color 2, a connected monochromatic 4–6-cell exemplar, exactly three monochromatic body components using distinct colors, exactly four nonzero colors, small body objects, and exactly one exact shape match.

**Alternatives considered:** validate only the rule’s mathematical precondition; allow malformed public textures. The ordinary training distribution needs stronger guarantees than rule executability, while malformed cases belong in explicit negative fixtures.

**Probe/evidence:** all five canonical pairs pass; four task-specific mutation fixtures and generic destructive mutations are rejected; defect lint is green.

**Failure mode/limit:** strict support is narrower than all inputs on which the Racket program may execute.

## D8 — Declare concrete competitors and bind witnesses to changed predictions

**Decision:** retain `always_middle_component`, `first_same_signature`, and `last_same_signature` as semantic rivals, canonical shortcuts, and lesson competitors. Each witness fires only when its named rival actually disagrees with the intended answer.

**Alternatives considered:** feature-presence witnesses without executable rivals; a large speculative rival list. Presence-only claims are weak, while an unbounded list would give false completeness.

**Probe/evidence:** semantic gate verifies rival-linked witnesses and generated shortcut counterexamples; large census and local probe report zero surviving competitors.

**Failure mode/limit:** undeclared rivals remain outside the measured claim.

## D9 — Stay near canonical morphology

**Decision:** use 11–12 rows, 13–15 columns, four distinct nonzero colors, and exemplars of 4–6 cells. These cover all five canonical inputs and keep the output-shape distribution aligned while allowing exact overrides.

**Alternatives considered:** retain the old 10–16 broad dimension metadata; expand shapes beyond 3×3. Broader geometry was not supported by canonical evidence and would complicate guaranteed three-candidate placement.

**Probe/evidence:** profile floor and distribution gate pass; all canonical pairs pass strict validation and the independent oracle.

**Failure mode/limit:** breadth outside the canonical envelope is intentionally not claimed.

## D10 — Retain a reproducible shortcut witness and portable probe

**Decision:** store the exact always-middle disagreement in `counterexamples/fixed-middle-shortcut.json` and add `workspace/reference_probe.py`.

**Reason:** future agents should be able to recheck source-bound cyclic starts, query rotations, public competitors, and an independent pixel oracle without reconstructing this review.

**Probe/evidence:** focused probe tests pass; the full local report is `checks/6be2608558c4_reference_probe.json`.

**Failure mode/limit:** overlapping windows mean 1,080 materialized pair uses correspond to 292 unique input grids; both counts are reported.

## D11 — Keep authority validity separate from curriculum strength

**Final self-review question:** should `self_check` reject a candidate set whose decoys do not all share the exemplar signature or whose two decoys share a normalized shape?

**Decision:** no. Preserve `self_check` as an authority-valid/canonical-support validator. Enforce the stronger same-signature, three-distinct-shape curriculum through construction, focused generated-output tests, semantic gates, and `workspace/reference_probe.py`.

**Reason:** every official canonical pair contains heterogeneous body signatures, while the Racket authority only needs a unique exact exemplar match. Two constructed curriculum-outside inputs—a shortened decoy and duplicate decoy shape—were accepted by `self_check` and produced valid Racket outputs identical to the independent Python mirror.

**Rejected alternative:** globally add same-signature and all-distinct-shape checks to `_analyze`. The RED tests exposed the missing restriction, but the attempted GREEN change rejected official canonical pair 0 and was reverted byte-for-byte.

**Probe/evidence:** `checks/self-review-validator-boundary/report.json`, `checks/self-review-validator-boundary/racket.json`, `checks/task-tests-signature-red.log`, and `checks/task-tests-signature-green.log`. The final generator and focused-test hashes returned to their previously verified values.

**Failure mode/limit:** `self_check` alone does not certify membership in the stronger teaching distribution. Curriculum membership is established by the constructive generator plus its focused/probe evidence.
