# Working notes: e5dc3d423bd9

## Review `review-c11f4ad7c35c1cc8`

The imported generator produced only odd-by-odd frames. Consequently, the simpler rule “mark the floor center of every hollow frame” fit every canonical pair and every ordinary generated input. The imported metadata also lacked `RULE_HASH`, advertised dead/singleton controls, mixed negative textures into the ordinary domain, silently accepted unknown controls, and did not honor advertised dimensions across bands. Original associated notes are empty, so the rationale for those choices is unknown.

Version `4.0.0` preserves the canonical Racket rule and repairs the input curriculum. Every ordinary draw now contains 1–3 odd target frames and one even-dimension decoy. The decoy is a direct negative example: its interior remains empty under the authority but is marked by the canonical-fitting rival. Layout is constructive, bounded, deterministic, and uses distinct colors; there is no rejection loop or fallback that silently simplifies a requested case.

Only three exact axes remain: `grid_h`, `grid_w`, and `n_odd`. Difficulty reweights the complete domain rather than changing validity. A canonical-profile mixture preserves 7×11, 8×10, and 9×11 support in every band. `self_check` accepts the four canonical inputs, including their zero-even-frame form, while ordinary generation deliberately includes one even decoy.

The independent oracle and distribution probe are in `workspace/reference_probe.py`; portable regression tests are in `tests/test_generator_e5dc3d423bd9.py`. The final generator SHA-256 is `79ea22b0c80d26e5de19d27fad3e253c89418fd8fea35dcf3129f3a2e7bcae8f`. Full rationale, rejected alternatives, failed iterations, audit findings, commands, and limitations are retained in the packet-level review documents and `checks/` evidence.
## Current reviewer considerations

Source SHA-256: `79ea22b0c80d26e5de19d27fad3e253c89418fd8fea35dcf3129f3a2e7bcae8f`.

# Decisions and retained reasoning — review-c11f4ad7c35c1cc8

## G1: Preserve authority; repair the curriculum

The selected Racket rule is internally coherent and solves all four canonical pairs. The defect was support: canonical and baseline generated inputs contained only odd-by-odd frames, so parity was never required. I kept the authority byte-identical and changed only the selected task sampler/metadata/tests/notes.

The imported associated-notes file is empty. Therefore the original rationale for odd-only generation, dead texture names, singleton axes, and silent override behavior is unknown. I did not retroactively describe those choices as deliberate.

Rejected alternatives:

- Changing the Racket rule to mark every frame would make the shortcut authoritative and contradict the intended parity condition.
- Removing the rival declaration or weakening semantic gates would hide the ambiguity rather than teach it.
- Copying canonical inputs into generated lessons would improve profile counts without improving compositional support.

## G1: Exactly one even-dimension decoy per ordinary input

Every ordinary draw contains 1–3 odd target frames and one frame with an even height or width. This is the smallest guaranteed contrast against `mark_every_frame_floor_center`: the authority leaves that frame hollow, while the rival adds a pixel. The object kind is shuffled before slot assignment and colors are sampled independently, so “decoy means fixed color/side/slot” is not built into the code.

Exactly one decoy was chosen over a random zero-to-many count because zero-decoy lessons recreate the original ambiguity, while several decoys consume substantial area at the smallest supported dimensions and make construction less reliable. This is a finite curriculum choice, not a claim that the authority domain contains only one even frame. Canonical inputs with zero decoys remain validator-lawful.

## G1: Constructive placement instead of retry/fallback placement

Object count is known before layout. Two objects use either a horizontal or vertical split; three or four use a shuffled 2×2 shelf. Reserved gaps make overlap and edge adjacency impossible by construction, and each slot is large enough for its assigned class. Frame dimensions are then sampled from dimensions guaranteed to fit. There is no unbounded search, stochastic rejection loop, or fallback to fewer/easier objects.

An initial validator required a complete one-cell halo around every bounding box. A canonical example has diagonally adjacent boxes, so that check rejected lawful authority data. `checks/tdd-green-attempt1/pytest.log` retains this failure. The final validator rejects overlap and edge adjacency but permits diagonal adjacency; the constructive sampler still produces clearer axis-separated examples.

Rejected alternatives:

- Retry-until-fit placement can silently bias hard cases or hang at corners.
- Falling back to fewer frames after exhaustion would make `n_odd` dishonest.
- Allowing ordinary frames to touch would complicate component parsing before the parity concept is learned.

## G2: Three honest axes only

The exposed axes are exactly `grid_h`, `grid_w`, and `n_odd`. Each is visible in pixels, has a non-singleton finite domain, is honored exactly in every band, and is recovered by `observe_overrides`. Unsupported keys and invalid values raise `ValueError`. `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty because every Cartesian product of documented values is constructible.

Difficulty changes weights but not validity. This avoids the baseline pattern where an advertised endpoint was accepted in one band and rejected in another. Exact replay is part of the regression suite and independent probe.

Rejected alternatives:

- Keeping palette, density, position, and texture names as decorative controls would preserve false metadata.
- Marking dead controls diagnostic would still add no useful curriculum information here.
- Band-specific valid ranges would require explicit incompatibility evidence and surprise callers.

## G2: Canonical-scale mixture without copying examples

The exact canonical profile triples are `(7,11,1)`, `(8,10,1)`, and `(9,11,1)`, where the third value is the number of odd frames. A core/broad mixture reweights these values in every band while retaining all dimensions and target counts. Final profile measurement observed exact hits in all bands (`16/20`, `8/20`, `7/20`).

Rejected alternatives:

- Forcing every draw to canonical sizes would reduce useful scale diversity.
- Widening or opting out of the profile gate would weaken the requirement rather than satisfy it.
- Sampling canonical grids themselves would risk memorization and leakage.

## G3: Independent oracle, executable rival, and lesson hooks

`workspace/reference_probe.py` does not import the generator. It independently finds same-color four-connected components, recognizes exact hollow frames, computes the parity-sensitive authority behavior, and computes the canonical-fitting rival. It also performs a path-based distribution census for future reviewers.

The generator declares the same rival through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; `SEMANTIC_WITNESSES` names the presence of an even frame, and `WITNESS_RIVALS` binds that witness to the rival. `lesson_identifiable` only reports a problem when a rival fits every demonstration but changes the query.

Rejected alternatives:

- Treating “an even frame exists” as sufficient without comparing outputs could certify a non-discriminating witness.
- Using the generator’s own output helper as the only oracle would let shared implementation errors agree with themselves.
- Claiming all possible shortcuts are eliminated would exceed finite evidence.

## G3: Validator scope

`self_check` requires a rectangular ARC grid, exact hollow frame components, distinct frame colors, no overlap/edge adjacency, 1–3 odd frames, and at most one even frame. It accepts all four canonical inputs, including their zero-even form. `strict_canonical_like` delegates to the same contract.

This validator intentionally describes the reviewed curriculum, not every input on which the Racket authority could return a value. Same-color disconnected frames, multiple even frames, touching frames, and arbitrary noise are outside the current sampler. That restriction is recorded in `REVIEW.md` rather than obscured.

## Tests and failed iterations

Tests were written and run against the baseline first. `checks/tdd-red/pytest.log` records 26 failures and 12 passes. After the first implementation, `checks/tdd-green-attempt1/pytest.log` exposed the overstrict diagonal-spacing error. The corrected focused suite passed 38 tests (`checks/tdd-green/pytest.log`), and the supported portable stage independently passed the same 38 tests.

The independent 600-draw probe then verified one decoy per draw, rival disagreement, exact replay, uniqueness, and self-check behavior before the full battery. The final battery and 300-lesson census were run only after the generator reached its final source hash. No final claim uses the failed intermediate source.

## Audits and shared-tool feedback

The two drawn audit targets were inspected and measured but not edited. `e282a664f807` has a reproduced orientation shortcut plus a rejected advertised endpoint. `b43d103c28d9` has a plausible global-role shortcut outside its deliberately narrower validator domain; that is reported as a domain question rather than an in-domain defect. General changes suggested by these observations are separated in `FEEDBACK_TO_CODEX.md`; they are not smuggled into the selected-task patch.

## Stopping rule

Stop because the selected task’s source-bound battery, portable tests, independent census, required solves, audits, and fresh-packet replay are complete on one final generator hash. Unknown masked-query correctness, finite rival coverage, and curriculum-domain limits remain explicit. Training admission and any shared-tool changes belong to maintainers.
