# Working notes: 537b409b6744

## Current parametric prototype — candidate rank

Assignment `review-69cf4b6df84bd4f6` adds a **proposed, task-local**
`candidate_rank` prototype under `workspace/parametric/`; production
`generator.py`, the canonical ledger, and approval state remain unchanged. The
default `nearest` program is byte-identical to canonical. The alternative
`farthest` program reverses only the primary gap ordering and retains the
larger-wall tie-break. Component extraction and the move/cut/grow transformation
are invariant.

The retained run materializes one episode per setting, each with three
demonstrations and four distinct queries. Real Racket produced all 14 labels;
the independent Python mirror matched 14/14. Both lessons are identifiable from
the demonstrations, all 8 production queries change under the rival setting,
and all 14 leave-one-pair-out rotations retain a refuting demonstration. The
canonical/default program still reproduces 8/8 canonical pairs. Evidence:
`checks/parametric/candidate-rank-final/report.json`.

Public examples are exact-byte, visible-content-addressed files. Hidden
parameters, seeds, programs, and query answers do not affect their IDs; metadata
and query-output leaks, boolean color cells, duplicate visible payloads, and
stale rule files fail closed. A crafted equal-gap case exposed and then fixed a
Python/Racket tie-break mismatch; retained adversarial evidence is
`checks/parametric/candidate-rank-adversarial/result.json`. Focused task tests:
81 passed.

Limits: evidence covers two retained seeds and the nearest-vs-farthest rival, not
every lawful grid or ranking hypothesis. The extension remains proposed and
requires separate owner review before any production API, approval, or training
admission.

## Current rule and domain

The modal color is background. Same-color 4-connected components are ranked as mover/wall candidates when a solid wall faces the mover, overlaps it on the transverse axis, and is strictly wider/taller. The smallest gap wins; equal gaps prefer the larger wall. The selected mover is erased, its channel through the wall becomes background, the wall grows transversely around the channel, and the mover appears at the far side. Output shape is unchanged.

Version `4.0.0` generates four-color scenes with a variable modal background, one solid mover, one larger solid wall, and one farther differently colored distractor. Every default scene exposes both nearest-candidate selection and wall growth. Public axes are limited to facts recoverable from pixels and have a complete exact-override contract.

## Reversed decisions

- **Prior v3.0.1:** background was always 0; only one mover/wall pair was emitted; degenerate textures overlapped the ordinary domain; several advertised controls were singleton, ignored, or unobservable; `self_check` accepted nearly any rectangular grid.
- **Current v4.0.0:** background varies (with scheduled canonical color 7), the third object is a genuine farther candidate, degenerates and decorative controls were removed, unknown keys are rejected, every axis has `observe_overrides`, and `self_check` validates the structural grammar while accepting all eight usable canonical inputs.
- **Reason:** the before battery failed lint, self-check, defect lint, distribution, overrides, and selected-authority synchronization. The final source passes all twelve after-battery stages, 68 source-bound tests, and a 300-lesson/1,200-rotation census.

## Authority decision

The selected augmented `racket_target.target_code` was synchronized byte-for-byte to the canonical selected program. Its historical `raw_code` remains unchanged and is intentionally reported as archival divergence. No rule behavior changed; execution parity passes and `RULE_HASH` remains `7b81cecb3b71`.

## Retained evidence and tools

- `tests/test_generator.py`: canonical acceptance/oracle parity, exact-axis observability in every band, bad override rejection, distribution support, mutation sensitivity, semantic rivals, color-role variation, and difficulty-band behavior.
- `workspace/reference_probe.py`: independent Python component/candidate/rule mirror and scene summarizer for future reviews.
- Final generator SHA-256: `61fe1c7026345bbfe8521c5b41576a8bda5a4695d037b84b255eb75461baa3ab`.
- `checks/after`: 12/12 green; 31,230 override draws, no findings or warnings; canonical profile hit 6/20 in each band; 600/600 strict semantic draws and both witnesses fired 600/600.
- `checks/lesson-census.json`: 300 three-demo/one-query lessons, 1,200 unique inputs, 0 production ambiguities and 0/1,200 ambiguous query rotations against the declared rivals.

## Known limits

The generated helpful domain intentionally concentrates on 10–14 grids, mover spans/depths 1–2, wall extras/depths 2–3, and gaps 0–2. `self_check` accepts the broader canonical geometry (including thinner/deeper walls and one-candidate scenes), but the sampler does not exhaust every canonical geometric envelope or every plausible undeclared rival. The finite census establishes separation only for `farthest_pair` and `no_wall_growth` under the tested sampler.
## Current reviewer considerations

Source SHA-256: `61fe1c7026345bbfe8521c5b41576a8bda5a4695d037b84b255eb75461baa3ab`.

# Decisions for 537b409b6744

## D1 — Replace the two-object toy distribution with a ranked three-object scene

**Prior choice:** v3.0.1 always emitted one mover and one wall, usually on background 0. That was easy to label but did not expose the rule's nearest-candidate decision.

**Decision:** every helpful v4.0.0 scene has a solid mover, a larger solid wall, and a farther differently colored distractor that also qualifies against the wall. The nearest gap is strictly smaller, so `farthest_pair` produces a different output.

**Alternatives rejected:** retain one pair and add only size/palette diversity; add a decorative nonqualifying object. Both improve appearance but still fail to teach ranking. A mix of one- and two-candidate scenes was considered; the selected sampler concentrates on decisive two-candidate lessons while `self_check` continues to accept one-candidate canonical inputs.

**Evidence/failure mode:** before semantic coverage had no contract. Final witnesses `nearest_pair` and `wall_growth` fire 600/600 times in `checks/after/checks/537b409b6744_after_semantic_gate.json`; the larger census reports 0 ambiguous lessons and rotations against both rivals.

## D2 — Make background and palette semantic roles rather than fixed labels

**Prior choice:** background 0 and two random object colors.

**Decision:** use a variable unique modal background, schedule canonical background 7 on core-profile samples, and draw three distinct role colors excluding it. The output rule uses geometry, not numeric color identity.

**Alternatives rejected:** always use canonical color 7 (too narrow); retain background 0 (failed canonical palette reachability); expose colors as public axes (unnecessary and would enlarge the override surface without adding structural control).

**Evidence/limits:** the task tests see at least 50 distinct `(background,mover,wall)` role palettes in 80 draws. The distribution gate and 10-color linter diversity pass. Color permutation legality was not exhaustively proven outside generated/self-checked scenes.

## D3 — Advertise only exact controls recoverable from pixels

**Decision:** public axes are `grid_h`, `grid_w`, `direction`, `mover_span`, `mover_depth`, `wall_extra`, `wall_depth`, `gap`, and `distractor_kind`. `observe_overrides` reconstructs each from the returned grid. Unknown keys and non-integral integer overrides are rejected.

**Alternatives rejected:** preserve `palette_kind`, singleton `position_bias`, `anchor_corner`, `asymmetry_force`, degenerate `texture`, `palette_size`, and `n_distinct_colors`. Those controls were ignored, aliases, singleton metadata, or not reliably observable.

**Evidence:** the compact override gate performed 31,230 draws over 347 cases and all three bands, with 0 findings, 0 warnings, and unknown-key rejection (`checks/after/checks/537b409b6744_after_override_results.json`).

## D4 — Preserve full exact override domains in every difficulty band

**Decision:** difficulty changes only the default gap: easy 0, medium 1, hard 2. Explicit values 0..2 remain legal in every band, as do the full domains of all other axes.

**Reason:** the first intermediate defect-lint pass found dead bands because difficulty did not affect any draw. Narrowing legal ranges by band would recreate the baseline override mismatch.

**Evidence:** a red task test captured byte-identical bands in `checks/task-tests-difficulty-red.log`; the final 68-case suite and defect lint pass.

## D5 — Use a structural validator, not an acceptance-only shape check

**Decision:** `self_check` validates ARC cell types, exactly four colors, a unique modal background, exactly three components, a qualifying pair, solid selected mover and wall, a unique top rank, nonidentity transformation, mover-color conservation, and shape preservation. It deliberately accepts broader canonical dimensions and one-candidate scenes.

**Alternatives rejected:** require the exact generated axis ranges or exactly two candidates. Either would reject legal canonical inputs. Require every nonselected object to be ragged/solid according to a generated tag: impossible to know the requested tag from arbitrary canonical input and unnecessary for rule validity.

**Evidence/limits:** 8/8 canonical inputs accepted; 39/54 deterministic destructive mutations rejected. Some mutations remain lawful after the change, so the validator is not claimed to reject every perturbation.

## D6 — Pin selected authority while retaining archival provenance

**Finding:** the canonical selected target and augmented selected target were behaviorally equivalent but byte-divergent; the augmented `raw_code` was also historical.

**Decision:** replace only `racket_target.target_code` in `shared/data/base/solutions/augmented/9f669b64__24de6d39aa77.json` with the exact canonical selected program. Leave archival `raw_code` untouched.

**Evidence:** authority synchronization now reports `SELECTED_SYNC_ARCHIVAL_DIVERGENT` with execution parity pass. No Racket behavior changed; `RULE_HASH` stays `7b81cecb3b71`.

## D7 — Retain an independent oracle as a future-agent tool

`workspace/reference_probe.py` separately implements component extraction, candidate ranking, the transformation, two rivals, axis observation, and batch summaries. It is test-only and is not imported by production code. This keeps semantic assertions independently checkable and gives future reviewers a small probe instead of forcing them to reconstruct the rule from the 22 KiB generator.

## D8 — Lesson policy and limitations

The production lesson is three demonstrations plus one query. The sampler has no declared cyclic schedule period; each generated grid itself refutes both declared rivals, so arbitrary query rotation is supported for the tested domain. The retained census tested 300 lessons (100 per band), 1,200 unique labeled pairs, and all 1,200 query rotations, with no ambiguity or scoring/materialization errors.

This is finite evidence against `farthest_pair` and `no_wall_growth`, not a proof of unique induction against every possible hypothesis. The helpful sampler does not exhaust canonical mover depths, wall depths/extras, large gaps, or nonqualifying distractor arrangements; those remain documented limits rather than hidden claims.

## Historical unselected repair proposal (prior assignment; not this review)

Standard collection rejects the assignment ID: packet/seed produce review-8d1abfeefcdf4bda, not review-149abe63a1c3c16f. Task/question/baseline match and audit draw reproduces after checking this identifier mismatch in an analysis-only contract copy; original return unchanged. Keep source repair and nearest/farthest prototype as needs-evidence proposal, preserving90 reported tests/full replay/12-stage battery but granting no acceptance to the proposed bytes. Current approved generator stays unchanged. Corrected authentic assignment/return binding or a separate owner review is needed before promotion; no original identity is fabricated. Retained at `workspace/proposals/review-149abe63a1c3c16f/manifest.json`.
