# Working notes: ee602abaa45a

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `15a28ca66e95270f6233945fdf9e33350a738c8b87e47623de97dbb3c9e5307f`.

# Decisions and rejected alternatives

## D1. Keep the canonical authority unchanged

**Inherited state and rationale.** The selected canonical rule already matched all five retained train/test pairs and the baseline `rule_smoke` and `authority_sync` stages were green. Original generator-design rationale was unavailable; associated notes were empty.

**Decision.** Do not edit the canonical row or Racket source. Pin `RULE_HASH = "9c5ac46b22bb"` in the generator and make the sampler conform to that authority.

**Alternatives considered.** Simplify the Racket rule around the baseline’s one-template inputs, or alter canonical examples to fit the imported sampler. Both would redefine the task around a generator defect and invalidate retained authority.

**Probe.** Final rule smoke applied 120/120 cases with 0 crashes and mirror parity 120/120. Authority sync passed execution parity over both distinct source texts. The authority-set hash is identical before and after.

**Failure modes and limits.** The Racket linter still reports nonblocking style findings in the inherited rule. They were not relevant to semantics and were deliberately left outside task-local scope.

## D2. Restore both candidates rather than decorating a selected answer

**Inherited state and rationale.** The baseline drew one selected template and omitted its alternative. Its comments described candidate selection, but the generated pixels made the selector unnecessary.

**Decision.** Every frame contains both candidates: color 1 in the left 3×3 slot and color 2 in the next 3×3 slot. The code-row selector determines which tight crop is transformed.

**Alternatives considered.** Keep one candidate but randomize its color; add a dummy second pattern that never affects labels; or encode the selector in metadata rather than pixels. Each retains the same shortcut: a learner can ignore genuine selection.

**Probe.** The independent oracle verifies that forcing candidate 1, forcing candidate 2, or ignoring the transform changes all 512 audited outputs. The task tests assert both candidates are present and both selector-ablation rivals differ on every default draw.

**Failure modes and limits.** Candidate shapes are restricted to connected 3- or 4-cell patterns that fit a 3×3 slot. This is canonical-compatible but not an exhaustive connected-polyomino domain.

## D3. Use the exact canonical geometry and palette envelope

**Inherited state and rationale.** The baseline sampled smaller 8–11 × 12–18 canvases and never matched a canonical profile. The profile-floor gate measured 0/60 exact and 0/60 envelope hits.

**Decision.** Generate heights 14–15, widths 22–24, exactly two width-9 frames of height 7 or 8, and a seven-color palette consisting of background, candidates 1/2, transform codes, and two distinct frame colors from 7/8/9.

**Alternatives considered.** Preserve the broad imported size range and add a small canonical mixture; or opt out of profile coverage. A mixture would continue spending most training mass off-domain, while an opt-out had no task-based justification.

**Probe.** Final profile floor is 60/60 exact and 60/60 envelope across all bands. `strict_canonical_like` accepts all five canonical inputs and all 600 semantic-gate draws.

**Failure modes and limits.** This choice prioritizes faithful data over extrapolative geometry. It does not claim the Racket rule would fail on other sizes; it claims those sizes are not evidenced as the intended training domain.

## D4. Replace placebo controls with five exact axes

**Inherited state and rationale.** The baseline advertised dimensions, palette counts, frame counts, code fields, density, position bias, and textures that were ignored, clamped, or swallowed. The before override report contained over 78,000 findings and accepted an unknown axis.

**Decision.** Expose only `grid_h`, `grid_w`, `selector_first`, `transform_pair`, and `layout_order`. Validate types and domains before generation; reject unknown keys; draw every default or override through keyed provenance; recover exact realized values through `observe_overrides`.

**Alternatives considered.** Keep old names as aliases; silently clamp them; or declare inert diagnostic controls. Aliases would preserve misleading API surface, clamping would falsify provenance, and the old controls were not useful diagnostics.

**Probe.** Final override gate passed 14,580 accepted draws over 162 cases and three bands with zero unstructured incompatibilities. Task tests recover all five values from pixels and assert malformed/unknown values fail closed.

**Failure modes and limits.** `transform_pair` is serialized as `"A-B"` to fit the shared enum contract. It cannot request equal transforms because canonical examples and the selected curriculum require distinct codes.

## D5. Make difficulty live without inventing a different rule

**Inherited state and rationale.** An intermediate revision generated byte-identical easy, medium, and hard draws, which defect lint correctly flagged as dead bands.

**Decision.** Difficulty applies a deterministic offset to the four-profile semantic schedule: easy/unspecified offset 0, medium offset 1, hard offset 2. It changes selected shapes and scheduled roles while preserving the same geometry, authority, and exact override semantics.

**Alternatives considered.** Make hard canvases larger, increase colors, or add more frames. Those would leave the canonical domain. Randomly perturb shapes without a declared schedule would make lesson coverage harder to audit.

**Probe.** A regression test first failed on identical bands, then passed after the offset. Final defect lint is clean, and every band covers all four profiles in the 600-draw semantic probe.

**Failure modes and limits.** These bands are curriculum strata, not calibrated psychometric difficulty. The names should not be interpreted as measured model difficulty.

## D6. Use a four-profile schedule with keyed geometric variation

**Inherited state and rationale.** Pure random sampling can omit a necessary witness in a short three-demo lesson. A static finite bank would be easy to memorize and offer poor input diversity.

**Decision.** Cycle four semantic profiles that vary first selector, transform pair, physical/read-order relation, selected morphology, grid dimensions, and height relation. Within profiles, use keyed randomness for frame colors, heights, exact positions, distractor orientation, candidate offsets, and non-fixed selected orientations.

**Alternatives considered.** Fully random roles; exhaustive Cartesian enumeration; or a fixed list of complete grids. Full randomness gives no short-window guarantee, exhaustive enumeration is unnecessary, and fixed grids collapse diversity.

**Probe.** Every consecutive three-example window in a 20-example sequence rejects all declared competitors. The 300-lesson census reports 1,200 unique inputs, and the independent probe finds 384 distinct inputs from 512 calls despite intentional cross-band overlap.

**Failure modes and limits.** The semantic period is visible to an auditor and can be oversampled badly by an external consumer. Lesson assembly must preserve consecutive schedule starts or independently verify rival coverage after reshuffling.

## D7. Deliberately teach reading order and vertical centering

**Inherited state and rationale.** Four of five canonical pairs are consistent with strict left-to-right ordering, and all five are consistent with top alignment. Those are plausible shortcuts for a small model.

**Decision.** Half the schedule crosses physical columns with reading order by placing the earlier frame to the right but higher. Profiles 0 and 3 fix selected orientations and use unequal output heights so floor vertical centering changes the answer.

**Alternatives considered.** Rely on random placement; encode an explicit order marker; or drop centering from the semantic contract because canonical data are ambiguous. Random placement gives no guarantee, a marker changes the task, and dropping centering would silently choose a canonical-fitting shortcut instead of testing the selected authority.

**Probe.** Final semantic gate finds reading-order witnesses in 310/600 and centering witnesses in 303/600. The large census refutes both rivals in every lesson and records that top-align fits 5/5 canonical pairs.

**Failure modes and limits.** The selected authority resolves the canonical ambiguity, but this remains an authority choice rather than a fact uniquely inferable from the five canonical pairs alone.

## D8. Add a total structural analyzer and mutation-sensitive self-check

**Inherited state and rationale.** The baseline had no `self_check`, so generic checks could not detect missing candidates, malformed frames, code drift, outside noise, or palette errors.

**Decision.** Parse high-color connected components into rectangular borders; validate dimensions, slots, code rows, frame separation, outside pixels, selector/transform relations, and palette size. Build `self_check`, `strict_canonical_like`, and `observe_overrides` on that analyzer. Malformed values return diagnostics rather than raising.

**Alternatives considered.** Validate hidden generation metadata; use only assertions inside `generate`; or duplicate parsers for each hook. Metadata proves intent rather than pixels, internal assertions do not protect external inputs, and duplicate parsers drift.

**Probe.** Final self-check is clean on 60 defaults and 5 canonical inputs and rejects 45/45 inherited destructive mutations. Task tests add border erasure, candidate removal, bad selector, bad transform, outside noise, ragged grids, booleans, and empty inputs.

**Failure modes and limits.** The analyzer is task-specific. It intentionally rejects lawful-looking generalizations outside the selected canonical grammar.

## D9. Separate production generation from an independent audit oracle

**Inherited state and rationale.** A generator and a mirror sharing one parser can agree on the same bug. The assignment specifically benefits future agents from reusable probes.

**Decision.** Keep the production `rule_mirror` for semantic hooks, but add `workspace/reference_probe.py` with an independently written frame parser, canonical loader, oracle, rivals, deterministic audit, and batched real-Racket comparison.

**Alternatives considered.** Import the private Racket runner into tests; compare only to the production mirror; or hand-inspect a few outputs. Private imports are unsupported, shared logic is circular, and manual inspection is not replayable.

**Probe.** The independent oracle matches 5/5 canonical outputs and 29/29 Racket evaluations, while auditing 512 calls for determinism, validation, profile coverage, and rival disagreement.

**Failure modes and limits.** Independence is by implementation, not formal proof. Both parsers still embody the reviewer’s understanding of the same visible grammar; Racket parity is the external check.

## D10. Test first and preserve failures

**Inherited state and rationale.** The defect was semantic and would not be safely repaired by checking only whether new code runs.

**Decision.** Write a task-local regression suite before replacing the generator. Preserve the 33-failure baseline log, then add two more failing infrastructure tests for literal `AXES` and live bands before their minimal fixes.

**Alternatives considered.** Patch first and add tests afterward; rely on the inherited battery; or overwrite failed evidence after success. Tests-after would be implementation-biased, the battery did not encode the omitted-candidate defect, and deleting failures would remove proof that tests detect the problem.

**Probe.** Baseline run: 33 failed, 2 passed. Infrastructure red run: 2 failed, 35 passed. Final direct and portable runs: 37 passed. All logs are retained separately.

**Failure modes and limits.** The tests cover five named rivals and the selected grammar, not every possible learned shortcut.

## D11. Stop with finite output-shape diversity documented

**Inherited state and rationale.** The final inherited diversity stage reports 100% unique inputs but 46% unique outputs over 300 pairs. Outputs are necessarily smaller and draw from a finite family of transformed/recolored shapes.

**Decision.** Do not expand morphology late in the repair merely to optimize a generic uniqueness number. Retain the measured limitation and prioritize semantic correctness, canonical support, and lesson identifiability.

**Alternatives considered.** Add many random connected shapes or arbitrary candidate sizes. That could improve output uniqueness but introduce disconnected crops, accidental symmetries, or windows where transforms/centering no longer matter.

**Probe.** The full battery remains 12/12 green; selector and transform rivals differ on every independent-probe call, while order and centering differ on half. Input uniqueness is 100% in the 1,200-pair census.

**Failure modes and limits.** A future controlled expansion should enumerate connected 3×3 shapes, measure stabilizers under transforms, and retain only shapes that preserve all witness guarantees.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-29dec646310b6c97:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `15a28ca66e95270f6233945fdf9e33350a738c8b87e47623de97dbb3c9e5307f`. At disposition, audited bytes match the current source.

### Current decision

Reported canonical5accepted/mirror,37tests+semantic,300lessons/1200uniqueinputs and all5rivals refuted. Finite declared-rival scope. Bounded reviewer-reported assessment only; other findings/source versions unchanged. Evidence=/home/user/Desktop/ARCpuzzles/var/review/new-return-tools-review/tool-disposition-proposals-nine.json sha256=76a7ea73fa5513ccc75ba5c5d6aad9abc549b59dfa65563ac320261676fd2870

### Assessment or prior finding

## ee602abaa45a

**No issue found** within the checked canonical, sampled, and declared-rival
scope.  Audited generator SHA-256:
`15a28ca66e95270f6233945fdf9e33350a738c8b87e47623de97dbb3c9e5307f`;
declared rule hash `9c5ac46b22bb`.

Checks performed:

- all four canonical training inputs and the canonical test input were accepted
  by `self_check`, and the Python mirror reproduced every canonical label;
- the strict combined audit ran 37 task tests and the semantic gate successfully;
- 300 lessons (100 per band) supplied 1,200 valid pairs and 1,200 unique inputs;
- all 300 lessons were identifiable under the declared hook; and
- each of five declared rivals was refuted by the demonstration window in all
  300 lessons.

Evidence: `checks/audit/ee602abaa45a/probe.json` and
`checks/audit/ee602abaa45a-combined/`.  This is a finite clean audit, not an
approval or a proof against undeclared rivals.  The audited source was not
modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
