# Current notes: 3eff273eeb83

## Intended rule and lawful input

A lawful input has one color-5 pivot and one contiguous, one-sided horizontal or vertical line of one to four color-2 cells attached to it. Recolor the original line to 3, rotate every source offset 90 degrees clockwise around the pivot, paint that copy 2, and keep the pivot 5. The source and rotated copy must remain in bounds; inputs use only colors 0, 2, and 5.

## Current production decisions

- Generator version remains `2.1.0`; valid-call generation and keyed outputs are unchanged.
- `seed` and `sample_index` must be plain integers; `sample_index` must be nonnegative.
- `difficulty` must be exactly `None`, `easy`, `medium`, or `hard`.
- Direction cycles through left, right, up, and down. Length class cycles `max, max, short, max, short`; max is length 4 and short is keyed-random length 1–3.
- Any four consecutive pairs contain all directions and at least two length-4 witnesses. With one held-out query, the remaining three demonstrations span both source axes and retain a witness against truncating the copy at three cells.
- Canonical/expanded sizes and centered/offset pivots remain generated and overrideable.

## Rival and lesson contract

`copy_at_most_three` is the strongest observed canonical-training shortcut: it fits all five training demonstrations but fails canonical test pair 0 at `(4, 9)`. It remains a declared lesson competitor with a length-4 witness. Counterclockwise, recolor-only, and copy-without-recolor remain generated-lesson competitors but are not represented as canonical-fitting over all seven labeled pairs.

The final source-bound census measured 300 four-pair lessons and all 1,200 query rotations. All production lessons and rotations were unambiguous against the four declared rivals, across 820 unique inputs.

## Authority and parametric prototype

The canonical Racket authority did not change. Normalized rule hash remains `3ac43b22416f`; canonical source SHA-256 remains `5e10aaa7e9867e2390957e6659b9e0e5581948b77e63c99c2f2ebc6e0c81bffe`.

A separate proposed/unapproved prototype under `workspace/parametric/` varies `rotation_direction` between clockwise and counterclockwise once per episode. It emits three demonstrations and one masked query, labels both settings through protected Racket execution, and keeps public artifacts free of hidden parameters and answers. It does not change production generation or approval.

## Current evidence and limits

Final generator SHA-256: `8a68b411365e9db8d1041793060404b635e1001543759091d4dc6111ce819d29`.

- direct selected tests: 49/49 pass;
- portable task tests: 55/55 pass (`checks/task-tests/`);
- final battery: 12/12 stages green (`checks/after/`);
- lesson census: 300/300 production lessons and 1,200/1,200 query rotations unambiguous (`checks/lesson-census-current.summary.json`);
- parametric evidence: 2 settings, 2 complete episodes, 8 distinct inputs, 0 ambiguous parameter-rival checks (`checks/parametric/rotation-direction-v1/`).

No known blocker remains for the canonical repair. Evidence is finite and rival-bounded; the parametric extension is proposed rather than approved.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-02d8f3d3b857aa46:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5b39e5c1a428ced4ebb3c4542f739535c7f8613e97cbfdf5749e29321d601011`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Specific false CANONICAL_SHORTCUTS finding on 5b39e5c1a428 addressed by accepted ad5b3c8d2324 source: empty canonical-shortcut declaration, useful negatives retained as lesson competitors and copy_at_most_three rival with rotation-safe length-four witnesses. Reviewer reports 12 task tests, 12/12 final battery, 300 lessons/1200 rotations and all 20 starts; intermediate 11/12 retained. Bounded reviewer-reported evidence, no independent generator rerun or universal clearance.

### Assessment or prior finding

## 3eff273eeb83

**Reproduced semantic-metadata defect: none of the declared `CANONICAL_SHORTCUTS` is a canonical-fitting shortcut.** Audited generator SHA-256: `5b39e5c1a428ced4ebb3c4542f739535c7f8613e97cbfdf5749e29321d601011`; selected/executed rule hash: `3ac43b22416f`.

The declarations `counterclockwise_rotation`, `recolor_without_copy`, and `copy_without_recolor` were evaluated on all seven canonical pairs. Every rival disagreed with every canonical output (0/7 fits for each), so the declaration cannot support a claim that canonical demonstrations leave those rivals unresolved. A concrete canonical input is retained; it passes the target validator, and public `arcpuzzles apply` returns the stored canonical output with a catalog-matching rule hash.

Evidence:

- `checks/audit/3eff273eeb83/declared-shortcuts.json` — exact canonical input/output, all three rival outputs, 7-pair fit vectors, and source/rule hashes;
- `checks/audit/3eff273eeb83/input.json` — public apply input;
- `checks/audit/3eff273eeb83/racket.json` — bound Racket output and hashes;
- `checks/audit/3eff273eeb83/apply.console.log` — command console record.

Suggested disposition: remove these functions from `CANONICAL_SHORTCUTS` unless a genuinely canonical-fitting rival is supplied; retain them under `LESSON_COMPETITORS` only if they are useful generated-distribution negatives. No audit-target source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-02d8f3d3b857aa46-v0001/audit_assets.json), manifest SHA-256 `6f45f4d6e407fcdd48b9860bb7ca44d6746ad1877ed04416fce8e92d2bd8e48b`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `8a68b411365e9db8d1041793060404b635e1001543759091d4dc6111ce819d29`.

# Decisions for 3eff273eeb83

## D1 — Treat retained returns as leads, not current measurements

The packet included accepted/reviewer-reported evidence for earlier source bytes. I used it to identify likely contracts and prior concerns, then reran the required checks on the pinned packet and final bytes. No earlier count or verdict is presented as a fresh measurement.

Rejected alternative: copy prior conclusions into this return without source-bound replay. That would obscure the new final hash and the newly detected strict-control defect.

## D2 — Reject malformed public controls at the generator boundary

The before battery showed 30 strict-scalar findings because `seed` and `difficulty` were delegated to permissive shared context code. The selected generator already had a plain-integer helper and strict `sample_index` behavior.

Decision: require `type(seed) is int`; retain `type(sample_index) is int` and nonnegative; accept difficulty only as `None`, `easy`, `medium`, or `hard`. The focused tests cover booleans, floats, strings, invalid labels, and valid controls.

Rejected alternatives:

- `isinstance(value, int)`: admits booleans;
- coercion with `int(value)`: silently changes malformed calls;
- changing shared `gen_ctx`: outside the selected task's allowed repair scope;
- bumping `VERSION`: would change valid keyed outputs even though semantics and valid-call behavior are intentionally unchanged.

Evidence: `checks/before/checks/3eff273eeb83_before_defect_lint.log`, `repo/generators/3eff273eeb83/tests/test_review_repair.py`, and `checks/strict-controls-defect-lint/`.

## D3 — Preserve the canonical schedule and authority

The existing five-slot length-class schedule and four-direction schedule already guarantee that any four consecutive pairs contain all directions and at least two length-4 witnesses. Holding out any one query therefore leaves three demonstrations spanning both source axes and at least one witness against `copy_at_most_three`.

Decision: do not alter the schedule, generated valid inputs, rule text, rule hash, active catalog authority, or archival source. The final rule hash remains `3ac43b22416f`.

Rejected alternative: combine the API repair with distribution tuning. The final census and battery provide no evidence that such tuning is needed, and it would confound the source of any behavior change.

## D4 — Keep the strongest shortcut explicit

The strongest canonical-training rival is `copy_at_most_three`. It fits the five training pairs because those sources have length at most three, but canonical test pair 0 has length four and refutes it at `(4, 9)`.

Decision: retain it as a semantic/lesson competitor with length-4 witnesses; do not call it a canonical-fitting shortcut over all seven labeled pairs. Preserve the exact counterexample in the task's `counterexamples/` directory.

Limitation: the rival set is intentionally finite and cannot establish logical uniqueness.

## D5 — Parameterize quarter-turn direction, not surface appearance

The requested parametric extension needed a small rule change while preserving the original reasoning structure. I considered:

1. **Rotation direction (`clockwise|counterclockwise`) — selected.** It changes the executed transformation, preserves pivot/source roles and distances, and can be inferred from demonstrations.
2. Output/source colors — rejected as mostly cosmetic reskinning.
3. Rotation amount (`90|180` degrees) — rejected because 180 degrees changes layout feasibility and object-overlap behavior more substantially.
4. Copy/recolor toggles — rejected because they remove a core stage rather than expose a nearby variant.

The selected parameter has no hidden effect on input sampling. The same lawful input can be executed under both settings and produces distinguishable outputs.

## D6 — Choose one semantic setting per complete episode

Decision: select `rotation_direction` deterministically from the episode seed before materializing pairs, then hold it fixed across three demonstrations and one query. Use four inputs covering every source direction; require both turns to remain in bounds. Every demonstration must refute the opposite setting.

Rejected alternative: resample direction per pair. That would make the episode internally inconsistent and the masked query unlearnable from its demonstrations.

Rejected alternative: put the parameter explicitly in the input. The assignment expressly permits fixed hidden episode semantics when demonstrations identify them, and inference is the point of this nearby family.

## D7 — Derive labels from exact protected Racket execution

The clockwise source is loaded as exact canonical bytes. The counterclockwise source is produced only by one guarded coordinate-site replacement; reversing that replacement must restore the exact canonical source. Every training label, query label, and rival prediction is executed through the protected Racket bridge. A Python transform appears only as an independent test oracle.

Rejected alternative: label with a Python mirror alone. That would not satisfy the authority requirement and could hide divergence between the prototype and executable rule text.

## D8 — Separate public challenges from private evidence

Public episode JSON is written from an allowlist containing only three training input/output pairs and one query input. Hidden parameter values, seeds, Racket source, rival predictions, and query answers stay under `private/`. A manifest hashes every emitted file and source snapshot.

This makes the prototype replayable for future agents without leaking its masked answer into the public challenge artifact.

## D9 — Keep the parametric extension proposed and unapproved

The production generator has a fixed canonical Racket interface. Decision: place the runnable extension only under `workspace/parametric/`, add focused task tests, and retain execution evidence under `checks/parametric/`. Do not modify shared APIs, catalog approval, canonical hash, or production generation.

Limitation: evidence covers two settings, two seeds, and eight distinct inputs. Shared integration would require a separate design and approval decision.

## D10 — Audit without repairing audit targets

The assigned audit targets are findings-only. I ran source-bound checks and wrote exact reproducers but did not edit either target. For `72a6d8b343e4`, the available tests and semantic gate were clean. For `8ac8cc86cc49`, the smallest decisive finding is the accepted `full_grid` input that the selected Racket rule cannot process; the unfinished broad semantic run is reported separately rather than treated as proof.
