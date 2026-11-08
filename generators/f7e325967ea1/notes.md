# Working notes — review-f540fc4332b90098

Baseline v2 SHA256 `3c9e3aa9b1b38924804125413dd9871b1718e9bcdd49836b7337f261487cfe42`; final v3 SHA256 `a8ff103ab40335048e1ece01c7d8c79b16d93c633b6cd2aa8ab86bc4aa2954b2`. Original associated-notes file is empty and was left unchanged. Historical source describes separated diagonal chains; missing rationale is not reconstructed as fact.

Repaired advertised-but-ignored controls, absent validator/hash, per-band canonical-profile support, and finite-rival lesson coverage. Retained exact axes only for dimensions and foreground palette count. Added domain validation, six competitors/witnesses, five verified canonical shortcuts, three-profile schedule, canonical/broad mixture, and task-local tests/probes. Racket and canonical examples unchanged.

Measured: 40 regression tests; all 12 final battery stages; 360 production-assembled lessons with no named-rival survivors; 3,360 boundary-control draws with 1,120 actual Racket counterexample checks. Baseline had 35/360 rival-fits-demos/wrong-query episodes, retained in the return. Final 1,440 observations contain 612 globally unique grids, so cross-band duplication is a known limitation.

Frozen solve: one genuine revision passed 3/3 visible examples, prior rule exposure yes, reference consulted during solve no, two masked queries unscored. See return's frozen solve notes; do not convert this into a blind benchmark or training approval.

Detailed choices and alternatives: returned `DECISIONS.md`. Both immutable audit targets were inspected but not patched. Next-agent actions and reusable commands: `workspace/NEXT_AGENT.md`.
## Current reviewer considerations

Source SHA-256: `a8ff103ab40335048e1ece01c7d8c79b16d93c633b6cd2aa8ab86bc4aa2954b2`.

# Decisions and retained uncertainty

Applies to final generator `a8ff103ab40335048e1ece01c7d8c79b16d93c633b6cd2aa8ab86bc4aa2954b2`; baseline `3c9e3aa9b1b38924804125413dd9871b1718e9bcdd49836b7337f261487cfe42`. IDs match `REVIEW.md`.

## R1 — Replace misleading axes with a smaller honest contract

Original evidence: v2 source describes separated same-color diagonal chains and broadens an older tiny-pair sampler. No additional rationale is present in the empty associated-notes file; the rationale for each ignored axis is unknown. Existing chain, color-family, texture, density, and position labels did not constitute controllable observable output properties.

Chosen: expose exact height, width, and foreground palette cardinality only. All have pixel-derived observers. Retire rather than pretend to implement chain-count and chain-length controls: intersecting diagnostic scenes do not have a unique such decomposition. Unknown and legacy keys reject explicitly. Clients depending on those keys must update; this is a version-3 contract change, not backward-compatible silent behavior.

Rejected: coercing invalid floats/booleans; clamping dimensions; returning fewer colors; accepting a dead diagnostic axis as an exact promise. Tests exercise rejection and observational equality. Full after override matrix passed. 3,360 boundary cases also passed, including nine foreground colors on 7x7 grids.

## R1 — Dimensions, palette, canonical support

Ordinary samples allow 7..18 rows and columns. Seven accommodates the 7x7 counterexample construction; eighteen adds room beyond the original 16-cell upper scale. Three foreground roles are sufficient for the interacting counterexample; 3..9 allows the whole non-background palette. Extra colors are singleton distractors rather than additional semantic roles. This changes the supported sampling distribution, not the canonical rule.

A keyed two-of-three mixture selects a canonical-scale component; its dimension draws strongly favor 8 and its foreground count favors 3. It still assigns nonzero weight throughout each advertised domain. The broad component favors size 8/12/16 for easy/medium/hard (11 when no difficulty), without forbidding canonical sizes in any band. This deliberately avoids A2's disjoint-difficulty support defect. We did not require every canonical shape to appear in the small census: the floor is per-band profile support, with explicit marginal coverage reported separately.

Measured: final exact canonical profiles 9/20, 11/20, 6/20 under the pinned profile plan, total 26/60; baseline 0/60. All canonical inputs are validator-accepted. Acceptance does not imply the exact original grid or morphology is reachable by the constructive sampler.

Tradeoff: canonical components reuse keyed draws across difficulty. Final 1,440 observations contain only 612 global unique inputs. The previous source had 1,440 global unique inputs on this plan. Do not hide that loss behind per-band uniqueness. Global deduplication and independent structural variants should be priorities before larger training exports.

## R2 — Teach distinctions inside complete lessons

A distribution can contain useful isolated witnesses while a learner's actual demonstrations omit them. Chosen schedule: sample index modulo three selects sparse, counterexample, clutter. Three consecutive unfiltered draws therefore include one diagnostic profile. The schedule depends on sample index, not a conveniently fixed seed. It is not advertised as an observable override.

The actual production runner can reject invalid/duplicate draws, so the schedule alone is not a proof about assembled episodes. A separate source-bound probe used real `run_one` assembly, 120 lessons per band, every cyclic start, canonical Racket labels, and actual observed input hashes. Final 0/360 named-rival survivors; baseline 35/360 wrong-query episodes after demonstrations indistinguishable from a named shortcut. All 35 are retained. No broad induction theorem is asserted.

Rejected: random profile choice with no lesson-level control (can miss witnesses); checking only aggregate witness frequency; hard-coding a sampler-specific rival list in the probe; declaring color-blind filling canonical-ambiguous despite an existing canonical counterexample. Chosen declarations contain six lesson competitors and five genuinely canonical-fitting shortcuts.

## R2 — Counterexample construction and its limits

The diagnostic input contains local relations distinguishing longer gaps, orthogonal neighbors, blocked centers, mixed endpoint colors, cascades, and a per-color bounding-box heuristic. Its 13 occupied cells fit in a 7x7 region. It is transformed by D4 symmetry, translated, and color-relabeled. Twelve point-relocation proposals are attempted; each accepted move preserves all six witnesses and lawful targets. Twelve is a proposal budget, not a guarantee that twelve moves succeed. Sparse scenes place three colored pairs. Clutter tries up to eighteen extra cell proposals. Extra singleton colors use randomized exhaustive candidate positions rather than silently reducing requested cardinality.

Why this over unrestricted rejection sampling: bounded placement plus witness-preserving changes produced reliable extreme-grid controls and avoids rare-event time sinks. Why not six visually isolated gadget boxes: small canonical-scale grids cannot accommodate large separated panels, and a fixed panel layout creates another shortcut.

Remaining concern: a transformed and locally mutated scaffold still has structural bias. A future model could recognize its family without learning the full rule; our named rival set does not test every possible classifier. Difficulty labels change sampling preferences, not measured cognitive difficulty. Do not convert finite semantic-gate success into model-performance claims.

## R1 — Rule authority and conflicting claims

No Racket bytes or canonical outputs were modified. The reference reads the original input once; the diagnostic oracle and fresh solution implement that interpretation on the chosen domain. No-op scenes are excluded by requiring at least one eligible blank midpoint. Competing different-color claims on one center are rejected: source traversal resolves them, but the task does not explain that priority. An alternative is to expose that priority as a new subtask, but changing labels or assuming order-invariant colored ties would be unjustified.

The validator deliberately accepts lawful small witnesses and canonical grids outside the constructive envelope. `strict_canonical_like` delegates to that rule-domain validator. Its 600/600 report is NOT a measurement of canonical morphology, original chains, or full generative support. Duplicate rows, minority-color removal, or adding a color do not automatically violate the law; the mutation test's modest rejection rate is not proof of a missing shape constraint.

## Evidence, implementation, and solve provenance

Forty regression tests failed on the original source before production changes, then passed after. Preserve `tdd-red.log`, the old generator, the complete before battery, and both probe versions. The override timeout is a failure with a recorded stage budget, not a reason to label the whole before run incomplete. The separate existing-output-directory failure is tooling usage evidence only.

The solve episode was prepared from final generator bytes. One revision sufficed on three visible examples; no failure was fabricated to create a positive/negative pair. Deliberate rival experiments use diagnostic labeling. Prior repair-phase rule exposure was yes, reference consultation during solve was no, and masked labels remain unknown. Notes are agent-authored summaries, not model token traces or human-authored research logs. Frozen finish notes and each original revision are retained.

## A1/A2 — Findings-only scope

A1 reproduced 70/490 exact transform requests being rewritten; its Racket labels remain correct for the scene actually generated. A2 reproduced zero medium/hard canonical-profile support; 48 independently executed samples showed no label/validator/observed-profile defect. Neither audit target was patched, rerolled, or used to replace the assigned repair. See `AUDIT.md` for source binding, domains, and counterexample interpretation.
