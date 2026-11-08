# Working notes: 8f221c2b552e

## Review outcome

Baseline source SHA-256: `9ce514609fcfca9516174e495cda0b877909021d511a55e1f939ba1e210fda6b` (v1.2.2).
Final generator SHA-256: `68a263400a0e5e0ce0fd8925e2e43ad8be003f488d15df34c47dcde1eb9ef130` (v2.0.0).
The selected canonical Racket authority was not changed; `RULE_HASH` is pinned to `df008460a237`.

No retained associated-note lead was available in this packet; the repair was derived from the pinned baseline, canonical examples, and fresh before-phase measurements.

## Baseline diagnosis

The before battery completed with 7 green stages, 2 advisories, and 3 failures. The generator omitted `RULE_HASH`; several advertised controls were ignored or contradicted by band-specific bounds; each active row received a unique color, so the canonical-fitting shortcut “bridge only colors occurring exactly twice globally” survived; the texture alias was semantically dead; and `self_check` established only a weak existential condition. The override stage recorded 6,017 findings over 117,630 draws / 1,307 cases. Evidence: `checks/before/`.

## Repair

- Replaced the sampler with a constructive six-axis contract whose returned pixels recover every requested value exactly.
- Added a deterministic six-profile curriculum with canonical-size support in all bands.
- Added `shared` pair-color scenes. In every three consecutive scheduled examples at least one shared-color scene refutes the global-count shortcut.
- Kept pair rows clean and placed 0..3 globally unique singleton distractors only on inactive rows.
- Added independent source-bound tests, a pixel-derived analyzer, a direct row-bridge oracle, real-Racket batch parity, cyclic query rotations, and a reusable qualification CLI under `workspace/`.
- Strengthened validation to reject malformed endpoint rows, partial color reuse, reused distractors, excessive distractors, invalid cells, and unobservable/unknown controls.

## Final measurements

- Completed after battery: 12/12 green, source hash `68a26340…`; `checks/after-final/`.
- Focused final source-bound suite after adding cyclic-rotation and qualification-tool coverage: 59/59 passed; `checks/qualification-tests.log`.
- Lesson census: 300 lessons, 100 per band, zero ambiguous lessons; every declared rival was refuted in 100/100 lessons per band; `checks/lesson-census.json`.
- Independent qualification: 300 generated samples, 1,200 query rotations, nine exact override boundary cases, and 65 selected-Racket parity cases all passed; `checks/qualification.json`.
- Post-repair visible solve: first revision passed 3/3 visible demonstrations, with earlier exposure declared yes and reference consultation declared no; `solve/summary.json`.

## Limits retained deliberately

The generated manifold is narrower than the full Racket domain: an active row contains exactly one two-endpoint color, and pair colors are either all distinct or all shared rather than partially reused. The finite rival set establishes separation from the measured `global_exactly_two` shortcut, not universal identifiability. These limits are explicit in `REVIEW.md` and `DECISIONS.md`.
## Current reviewer considerations

Source SHA-256: `68a263400a0e5e0ce0fd8925e2e43ad8be003f488d15df34c47dcde1eb9ef130`.

# Decisions for 8f221c2b552e

## D1 — Keep the selected Racket authority unchanged

**Input choice.** Treat the canonical row-local fill rule as authoritative and repair only the sampler, validator, tests, and review tooling.

**Rationale.** All five canonical pairs matched the selected rule, and the baseline rule-smoke/authority behavior was correct. The defects were distributional and contractual, not label errors.

**Alternatives rejected.** Broadening or rewriting the Racket rule would add review risk without fixing the ignored axes or ambiguous curriculum. No canonical or base authority file was changed.

**Probe.** Canonical acceptance and 65 final selected-Racket parity cases are recorded in `checks/qualification.json`; the after battery’s authority stage is green.

## D2 — Replace the inherited metadata contract rather than preserve inert aliases

**Input choice.** Advertise only six controls that can be recovered from pixels: height, width, number of pair rows, pair-color mode, singleton distractor count, and span style.

**Rationale.** The baseline’s palette/texture claims were either ignored, overlapping, or not inferable from returned grids. Exact controls should mean exact observable postconditions.

**Alternatives rejected.** Keeping compatibility aliases would leave silent no-ops. Treating all controls as best-effort would contradict the repository override contract.

**Failure mode considered.** Joint constraints can make independently valid controls incompatible. The chosen domains are deliberately small enough that every combination is constructive; `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is therefore empty.

**Probe.** The inherited override gate accepted 25,290/25,290 draws in its focused run; task tests cover min/max/mixed combinations in every band.

## D3 — Use a constructive row grammar

**Input choice.** Generate 2..5 active rows, each with exactly two separated endpoints of one color and an initially empty interior. Place 0..3 unique singleton distractors only in inactive rows.

**Rationale.** Construction makes the validator contract easy to state, prevents accidental extra pairs, and guarantees a non-identity output.

**Alternatives rejected.** Rejection-sampling arbitrary sparse grids was harder to make total and would blur which axes were actually controlled. Allowing distractors on pair rows would introduce avoidable color/object ambiguity.

**Limitation.** The full rule can handle multiple repeated colors in one row and more than two occurrences of one color; this sampler intentionally does not cover those cases.

## D4 — Use exact `distinct` and `shared` color modes

**Input choice.** Pair colors are either all different or one color reused in every pair row.

**Rationale.** The shared mode supplies a strong row-locality witness: the repeated color occurs more than twice globally but must still be filled in each row. Both modes are exactly observable.

**Alternative rejected.** Partial reuse is lawful and could broaden coverage, but it complicates a simple exact categorical axis. It remains the clearest future extension.

**Failure mode considered.** A solver might overfit the all-or-none reuse pattern. The actual transformation remains identical in both modes, but this finite grammar is not universal proof of row-local induction.

## D5 — Schedule six profiles instead of relying on random witness frequency

**Input choice.** A deterministic six-slot cycle alternates canonical-profile distinct scenes with shared-color scenes, with a broader shared profile in the sixth slot.

**Rationale.** Every three consecutive demonstrations contain at least one shared-color witness, while every band still receives canonical-size support and broader geometry.

**Alternatives rejected.** Uniform random mode selection can produce witness-free short lessons even when long-run frequency looks healthy. Pinning every draw to canonical dimensions would satisfy profile floors but reduce diversity.

**Probe.** The shared census found zero ambiguous lessons across 300 lessons; the task-local cyclic audit tested all 1,200 query rotations across 100 starts per band.

## D6 — Define span style from realized gap lengths

**Input choice.** `short` means all endpoint gaps are one or two cells; `long` means all are at least three; `mixed` contains at least one of each. Full-width endpoint pairs are excluded so an outside-background witness remains.

**Rationale.** These categories are recoverable from the grid and create visible geometric variation without changing the rule.

**Failure mode considered.** Very narrow grids might not support both categories. The declared width floor of 8 makes all three styles constructible for all allowed pair counts.

## D7 — Strengthen validation at the task boundary

**Input choice.** Reject ragged/invalid grids, malformed repeated colors, third endpoints, filled interiors, pair/distractor color collisions, partial pair-color reuse, and more than three distractors.

**Rationale.** `self_check` must define the generated manifold rather than merely discover one valid pair somewhere in a grid.

**Alternative rejected.** Accepting the entire canonical rule domain would make exact axis recovery ambiguous and weaken mutation tests. Canonical examples remain accepted despite the stricter generated manifold.

## D8 — Declare and execute the strongest observed canonical-fitting rival

**Input choice.** Retain `global_exactly_two` in `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`; require it to fit every canonical pair and be refuted by each generated lesson.

**Rationale.** The baseline’s unique-color policy made this shortcut observationally equivalent on all examples. A named executable rival turns that concern into a regression.

**Limitation.** One declared rival is not an exhaustive hypothesis class. Reports say exactly what was tested and do not claim universal identifiability.

## D9 — Build independent reusable probes

**Input choice.** Keep pixel analysis, a direct oracle, canonical loading, cyclic lesson rotations, and Racket batching in `workspace/reference_probe.py`; expose a machine-readable qualification CLI in `workspace/qualification.py`.

**Rationale.** Future agents can verify changes without importing production geometry helpers or silently falling back when Racket is unavailable.

**Probe.** The CLI’s own task-local test was written before implementation; the final focused suite contains 59 tests and passes from a copied portable source.

## D10 — Preserve interrupted and failed evidence separately

**Input choice.** Keep the first interrupted after battery and the failed before battery rather than overwriting them with the final pass.

**Rationale.** A running/incomplete aggregate is not a pass. Separate paths make the progression auditable: `checks/before/`, `checks/after/`, and `checks/after-final/`.

**Failure mode considered.** Evidence volume can exceed return limits. The packet packager’s verified evidence bundle is used if needed; decisive reports and reproductions are retained.
