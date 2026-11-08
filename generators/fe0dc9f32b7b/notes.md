# Working notes: fe0dc9f32b7b

## Final review state — v3.1.0

- Generator SHA-256: `66f1678df9229df8b7061543edd48a05fe2cb31d16df67b515295b74abdab506`.
- Canonical rule hash: `5f1e925f80ea`; selected Racket authority unchanged.
- Re-measured v3.0.0 baseline: 12/12 battery stages green, but an exact-perimeter-only solver matched all 5 canonical pairs and all 1,000 sampled baseline inputs.
- Final after battery: 12/12 green.
- Portable task-local tests: 55/55 green.
- Source-bound lesson audit: 300/300 identifiable lessons, 100 per band; 1,155 unique inputs among 1,200 lesson inputs; strict census 450/450.
- Independent audit: 600 generated samples, zero self-check/oracle/determinism errors; 37/37 selected-Racket parity cases.
- Shortcut probe: both canonical-fitting shortcuts (`exact_perimeter_only`, `clamp_palette`) match 5/5 canonical pairs and receive generated counterexamples; all four declared rival witnesses were found within three ordinary draws.
- Exposed post-repair solve: first genuine revision passed 3/3 visible demos; earlier rule exposure declared and no reference consulted.

## Core correction

The v3.0.0 distribution taught only exact hollow qualifying frames. That made the stricter rule “qualify only exact perimeter outlines” observationally equivalent to the selected authority over every canonical pair and every sampled generated input, even though the authority uses only component size relative to the bounding box.

Version 3.1.0 maps the existing `nested_depth` schedule slot to `warped_inner`: a connected inner color-8 component formed by removing one non-corner perimeter cell and adding one adjacent interior cell. It preserves the bounding box, component count, and 4-connectivity while violating exact perimeter occupancy. The corresponding executable shortcut, witness, lesson competitor, tests, and independent probe were added.

## Distribution decision and limitation

The repair reused the three-slot lesson schedule instead of adding a fourth slot, so every three consecutive demonstrations still include all required distinctions. Eight safe inward-swap templates vary side and corner orientation under keyed RNG.

A retained restriction audit sampled 900 final inputs (300 per band): all 300 non-clean authority-positive components were single inward swaps, and an “exact outline or one inward swap” shortcut matched 900/900 generated outputs. The repair therefore teaches the intended count predicate directly but does not claim arbitrary-topology coverage. See `checks/final-repair-restriction-audit.json` in the review return.

## Retained tools

See `workspace/README.md`. Full decisions, evidence, audit results, and limitations are in the return-root `DECISIONS.md` and `REVIEW.md`.
## Current reviewer considerations

Source SHA-256: `66f1678df9229df8b7061543edd48a05fe2cb31d16df67b515295b74abdab506`.

# Decisions: fe0dc9f32b7b v3.1.0

## D1 — Treat the accepted v3.0.0 return as a lead, not evidence

**Decision.** Re-run the immutable selected source and all required checks. Historical return `review-b2092a0c7f9fc0a3:v0001` supplied context only.

**Reason.** The assignment explicitly warns that prior claims are not measurements of the selected baseline. The completed v3.0.0 battery was 12/12 green, yet direct differential testing found a training-identifiability gap the declared gates did not cover.

**Failure retained.** The first foreground baseline run was interrupted after three green stages. It remains under `checks/before-interrupted-1/`; the completed rerun is under `checks/before/`.

## D2 — Leave the Racket authority unchanged

**Decision.** Do not edit canonical or selected Racket code. Keep `RULE_HASH = 5f1e925f80ea`.

**Reason.** Canonical outputs, current Python mirror, and sampled selected-Racket parity agree. The defect was that generation covered only a strict subset of positive geometries, not that the authority labeled them incorrectly.

**Rejected alternative.** Narrowing the authority to exact outlines would make current samples easier but would contradict the selected program's actual component-count predicate.

## D3 — Add a count-preserving non-hollow positive

**Decision.** Introduce `warped_inner`: start from a clean inner frame, remove one non-corner perimeter cell, and add one adjacent interior cell.

**Reason.** This is the smallest deterministic mutation that isolates the missing distinction. It preserves bounding box, component size, nesting, and 4-connectivity while making exact perimeter occupancy false.

**Rejected alternatives.** Arbitrary random equal-count connected components were rejected for this bounded repair because they introduce many extra shape hypotheses and higher rejection complexity. Merely adding more clean frame sizes would not refute the shortcut. Turning the malformed overfilled branch into a positive would remove the existing negative witness.

## D4 — Reuse the three-slot curriculum

**Decision.** Map the existing `nested_depth` profile to `warped_inner` rather than adding a fourth ordinary schedule slot.

**Reason.** Lesson assembly consumes three consecutive demonstrations. Reusing a slot keeps every cyclic three-demo window complete: nested depth plus count semantics, malformed-object filtering, and palette exhaustion.

**Alternative considered.** A fourth slot would require increasing `EXAMPLES_NEEDED` or accepting windows that omit one decisive distinction. Neither was justified.

## D5 — Vary the local mutation under keyed RNG

**Decision.** Choose among eight safe inward-swap templates around the four sides/corners, using the existing keyed scene RNG.

**Reason.** A fixed top-edge mutation would create an unnecessary location cue. The second red/green test required multiple realized signatures while preserving the same predicate.

**Measured support.** The final restriction audit observed 300 warped scenes across 900 samples and 77 shape-specific normalized signatures arising from the eight templates.

## D6 — Make the missing shortcut executable

**Decision.** Add `exact_perimeter_only` to `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; add witness `size_equals_perimeter` and bind it in `WITNESS_RIVALS`.

**Reason.** The shortcut fits every canonical pair, so prose alone cannot prevent regression. The official semantic gate can now verify canonical fit, witness firing, rival disagreement, and lesson identifiability.

**Probe result.** Final semantic gate reports `size_equals_perimeter` on 213/600 census samples and verifies its rival on 60/60 firing cases.

## D7 — Extend tests and the independent probe, not only generator internals

**Decision.** Add red-first tests for a non-hollow positive and varied mutation location; update canonical-shortcut iteration and exact scene overrides; extend `reference_probe.py` with an independent exact-perimeter rival/census.

**Reason.** A generator-only change could be accidentally undone while the old test suite remained green. Independent reconstruction reduces common-code risk.

**Final result.** Portable task tests 55/55; independent audit 600/600 with 200 exact-perimeter counterexamples and Racket 37/37.

## D8 — Stop at a focused repair and document the residual shortcut

**Decision.** Do not attempt arbitrary authority-positive topologies in this round.

**Reason.** The one-swap branch provides a clean, low-entropy teaching contrast and preserves the established curriculum. Broader topology generation deserves its own design and validation work.

**Limitation.** The rival “exact outline or one inward swap” matched all 900 sampled final outputs. Future work could add two-swap and nonlocal connected variants, but should preserve component connectivity, bounding box, count, lesson identifiability, and low visual ambiguity.

## D9 — Keep both audit targets unchanged

**Decision.** Report findings only, as assigned.

**00af0f134576.** No issue found after current portable tests, semantic census, lesson checks, and Racket parity. The interrupted optional aggregate is disclosed rather than converted into a pass.

**2cefa1581476.** Retain the exact domain-valid counterexample showing that the documented height/color tie break disagrees with the selected width/position authority. Suggested future repair: pin `RULE_HASH`, implement a mirror and semantic rivals, correct the prose, and schedule equal-height objects that separately teach width and position ties.

## 2026-10-24 parametric review `review-b280d98a5fff10a2`

- Added a native two-setting parametric family under `workspace/parametric/`.
  `outer_to_inner` preserves the selected canonical Racket program byte-for-byte;
  `inner_to_outer` reverses only the palette before the unchanged component
  classification, containment-depth, and fill stages.
- The deterministic sampler supports 2–6 demonstrations and exactly four
  distinct queries. Every exercised episode includes a substantive 30×30 query;
  the first two demonstrations expose nested depth, malformed color-8 objects,
  palette exhaustion, and both one- and two-swap count-qualified warped shapes.
- The declared-rival audit covered 40 episodes (two settings, four seeds, all
  supported demo counts): zero rivals survived. This is finite evidence, not a
  uniqueness proof over arbitrary programs.
- Native qualification passed four jobs and 40 protected-Racket evaluations.
  The source-bound causal witness replays both settings and shows that clamping
  positive containment depth to one changes 206 cells per case.
- Public batch files pass the canonical-byte/ID/masked-query checker; the runtime
  helper also exposes the four queries one at a time with identical first-turn
  bytes for single-query use.
- Reviewer status is `ready`, not accepted. Next action: integrate these exact
  source bytes, rerun native qualification, replay the witness, and perform fresh
  owner acceptance. No variant is training-admitted by this return.
