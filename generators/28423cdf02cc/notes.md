# Current notes: 28423cdf02cc / 363442ee

## Intended rule and domain

Copy the full asymmetric top-left 3×3 colored template, in its original orientation, centered on every blue marker to the right of the full-height gray divider. Preserve the original template and divider. The template excludes colors 0/1/5 and has eight distinct dihedral orientations; stamps are complete, in bounds and nonoverlapping.

Version **3.1.1**, canonical normalized `RULE_HASH=63b41fa0b187`.
Final generator SHA-256: `75ee24dc86a6d294fab9aab46fc47392cab0b7f5dbdaa58a59e63b349acf83c9`.

## Exact controls and repaired coercion

Public axes remain `grid_h=9..16`, `grid_w=13..20`, `n_dots=3..6`, and `palette_size=3..5`; each is observable in the returned input. All six integer draw sites now use shared `draw_int_strict`. Seed and sample index require actual integers (not booleans); sample index must be nonnegative, while negative integer seeds remain valid. A `None` axis retains default sampling.

Prior use of permissive `draw_int` silently accepted values such as height 9.75 and returned height 9. The exact baseline witness is `counterexamples/fractional-height-coercion.json`. Strict rejection replaces that behavior; 44 scalar regression cases and the final defect/override gates support the change. Unknown controls remain rejected.

## Inherited teaching schedule retained

The selected 3.1.0 baseline already used the cycle:

1. Exact canonical profile.
2. Exact canonical profile.
3. Guaranteed off-canonical-lattice markers.
4. Guaranteed off-canonical-lattice markers.
5. Guaranteed off-canonical-lattice markers.

This preserves a 40% canonical-profile prior. Every three consecutive demonstrations include an anti-lattice scene; every four consecutive pairs include at least two, so holding out any one pair still leaves a distinguishing demonstration. `EXAMPLES_NEEDED=3`, `LESSON_SCHEDULE_PERIOD=5`, `MIN_STRICT_FRAC=0.35`.

The inherited `counterexamples/fixed-canonical-lattice-ambiguity.json` documents the earlier independent-mixture failure: all demonstrations could sit on the fixed lattice while a query did not. This return retains the existing schedule rather than claiming that prior repair as new. Four linked canonical profiles, generalized marker layouts and lawful size/palette bounds are unchanged.

## Semantic contract and final evidence

Eleven distinct executable rivals cover seven nonidentity template symmetries, wrong anchor, first-marker-only, center-cell-only, and canonical-lattice-only stamping. Five witness families and `lesson_identifiable` test labelled demonstrations/query against that finite set.

Final evidence in return `review-cf01bd5fe705006c`:

- Battery: **12/12 green**; 600 semantic draws, 233 strict-canonical (38.83%); all five witnesses; 12/12 lessons and 48/48 holdouts.
- Profile floor: 19/60 exact canonical hits, including every band.
- Override gate: 19,260 accepted draws / 214 cases, zero findings.
- Portable task tests: **84/84 passed**.
- Production census: 300 lessons / 1,200 unique inputs; zero ambiguous production queries and zero ambiguous query holdouts against the declared rivals.
- Separate fixed-seed all-start check: five residues × three bands, 15 lessons / 60 holdouts, 16 unique inputs, zero ambiguities.

See `checks/after-final/`, `checks/task-tests-final/`, `checks/lesson-census-final.json` and the schedule receipt inside `checks/after-final/checks/`. The random census itself does not enumerate the schedule; its warning is addressed by that separate receipt.

## Authority correction and preserved archive

The canonical ledger and rule behavior are unchanged. The active selected task-base `/racket_target/target_code` is now exactly canonical `program_solution`; archived `raw_code` is **unchanged**. Prior notes claiming both fields were synchronized were inaccurate for this pinned packet and have been replaced.

Canonical program SHA-256: `80a4d09cd7cd2e1456c6f85176e1556c8eb46fffa5bcd06869b835e363815d35`.
Archival raw SHA-256: `63b41fa0b18703287defdaec215a69e9f3c15fb9e0db6764752ac135ff585677`.
The selected authority proposal/field-scope review and final authority-sync receipt record the correction.

## Separate proposed rotation family

`workspace/parametric/stamp_rotation.py` implements `quarter_turns ∈ {0,1,2,3}` clockwise rotations of copied stamps. A single setting governs each three-demo/one-query episode, default 0 has exact canonical Racket text, and input draws do not encode the chosen setting. The source template remains unchanged.

All labels execute materialized Racket programs. Public episodes omit rule parameters and query answers; private manifests retain them with source/rule hashes. Reusable `assess_settings` reports refutation, surviving answer equivalence and query-changing ambiguity across all four holdouts. Final evidence covers 24 episodes / 96 pairs / 96 identified holdouts and four canonical default pairs. Status is **proposed**, separate from canonical production and training admission.

## Limits and open findings

No selected-task gate remains blocked. The rival and parameter families are finite; these checks do not establish unique induction against arbitrary programs. The schedule guarantee assumes consecutive default sample positions; explicit overrides bypass it and need caller-managed lesson coverage. Full templates, asymmetry, nonoverlap and complete stamps are deliberate domain restrictions.

Audit findings on other assigned targets are returned separately in `AUDIT.md`, without modifying those sources. Masked solve-query correctness remains withheld. Approval and training admission remain maintainer decisions.
## Current reviewer considerations

Source SHA-256: `75ee24dc86a6d294fab9aab46fc47392cab0b7f5dbdaa58a59e63b349acf83c9`.

# Decisions for 28423cdf02cc

## D1 — Add one small original-family rule parameter first

**Prior rationale / unknown.** The selected task has a sound template–marker relationship and a teaching schedule, but no runnable parametric extension. Its original absence is unexplained. The assignment explicitly prioritizes a small rule extension preserving canonical default behavior.

**Choice.** Implement clockwise rotation of copied stamps with `quarter_turns=0..3`; choose one setting per episode. Keep the template, divider, marker meaning, input distribution and complete-stamp constraints. The default returns the exact canonical program text; the other rules substitute one coordinate lookup. All labels come from actual Racket execution.

**Alternatives.** A second marker-anchor parameter would change the marker's role and validity/clipping constraints, so it was not added. Input-only palette or size axes do not make a rule family. Per-pair random rotation was rejected because it would provide no single rule to infer.

**Probes / limits.** The final suite covers 24 episodes / 96 pairs across two seeds, three bands and all four settings, with 96/96 identified holdouts and four canonical parity cases. Independent coordinate tests cover clockwise direction. This is a proposed finite family, not production admission or arbitrary-program identifiability.

## D2 — Make exact controls strict at both layers

**Prior rationale / unknown.** `ctx.draw_int` coerced values, presumably for convenience; its use in an advertised exact integer API had no documented justification. On the pinned baseline, `grid_h=9.75` silently produced height 9. Boolean and floating/string seed/index inputs also survived.

**Choice.** Use shared `draw_int_strict` at all six draw sites; validate `type(seed) is int` and `type(sample_index) is int`, with nonnegative index. Keep negative integer seeds and `None` as the existing default sentinel. Version becomes 3.1.1.

**Alternatives.** Rounding, clamping, or silently parsing numeric strings would still contradict exact controls. Rejecting all negative seeds would narrow a useful deterministic family without a demonstrated need. A new shared coercion layer was unnecessary and outside the allowed edit scope.

**Probes / limits.** Preserve the exact fractional-height counterexample and failing numeric-string/boolean-seed tests. The 44 new scalar cases check invalid types, each boundary in all bands, None schedule equivalence, invalid seed/index and deterministic negative seeds. Final override coverage is 19,260 draws, 214 cases, zero findings. Legal domain bounds are unchanged; reproducibility should always bind version and source hash.

## D3 — Synchronize the active authority without rewriting archival evidence

**Prior rationale / unknown.** Inherited notes claimed both active and archival texts had been synchronized. The current pinned packet contradicted that history: active target text differed from canonical, while behavior already matched. The formatting divergence's cause is unknown.

**Choice.** Generate the official non-applying synchronization proposal, verify its field scope, dry-run it, then apply only the selected task-base `/racket_target/target_code` change. Leave `raw_code`, the canonical ledger and normalized `RULE_HASH=63b41fa0b187` unchanged. Update the focused test to require exact active authority and preserve the archival raw hash.

**Alternatives.** Changing canonical behavior to fit a shortcut would be a label defect. Changing the archive would erase provenance. The broad applying workflow may create recovery/lock artifacts outside allowed scope; the reviewed single-file patch avoids those side effects.

**Probes / limits.** `checks/selected-review/` records the proposal, field comparison and dry run. Final authority sync and rule smoke are green. Canonical program SHA-256 is `80a4d09cd7cd2e1456c6f85176e1556c8eb46fffa5bcd06869b835e363815d35`; archival raw SHA-256 remains `63b41fa0b18703287defdaec215a69e9f3c15fb9e0db6764752ac135ff585677`.

## D4 — Retain the inherited teaching schedule and exact axes

**Prior rationale.** Version 3.1.0 already replaced independent 40% canonical mixing with the five-slot schedule `canonical, canonical, anti-lattice, anti-lattice, anti-lattice`. Inherited notes/counterexample explain why: three canonical-lattice demonstrations could leave a coordinate shortcut unresolved on a generalized query. This history is a lead, not a new measurement or newly implemented repair.

**Choice.** Retain that schedule, four linked canonical profiles, three demonstrations, one query, and all eleven distinct rivals. Retain observable exact axes: height 9–16, width 13–20, 3–6 markers, 3–5 template colors. Preserve complete asymmetric templates, full in-bounds nonoverlapping stamps, and fixed marker/divider colors.

**Alternatives.** An independent mixture only reduces the chance of a teaching gap; it does not remove it. All-generalized examples would lose canonical support. A universal random-grid distribution would test unrelated clipping, overlap and source-region cases and require a different domain contract.

**Probes / limits.** The final 300-lesson production census materializes 1,200 distinct inputs with zero query disagreements against the declared rivals. Every pair is also held out once, preserving remaining order: zero ambiguities in 1,200 rotations. The final strict battery additionally enumerates all five starts at seed 0, all bands: 15 lessons/60 rotations but only 16 distinct inputs. The random census alone carries an unenumerated-schedule warning; the dedicated receipt resolves the required fixed-seed check.

Every cyclic four-position window has at least two anti-lattice scenes, so any one held-out query leaves a counterexample in the three demonstrations. This construction assumes consecutive default positions. Explicit overrides intentionally bypass it; a caller assembling overridden lessons must check semantic coverage separately. These results cover finite hypotheses and saved inputs, not all seeds or arbitrary algorithms.

## D5 — Distinguish fitting parameters from determined answers

**Prior rationale / unknown.** A count of surviving settings by itself conflates uncertainty in the parameter with uncertainty in the query answer.

**Choice.** Build reusable `assess_settings` in the task-local prototype. Compare every setting's executed outputs on the same inputs. Record demonstration refutation, surviving answer-equivalent settings, and surviving query-divergent settings, for the normal query and every holdout.

**Alternatives.** Treating every surviving alternative as query ambiguity would conflate parameter uncertainty with answer uncertainty. This rotation prototype separately requires unique parameter identification for every holdout. Testing only canonical examples would discard rivals that remain plausible from a generated lesson's actual demonstrations. Exposing parameters or query outputs in the public episode would leak the answer.

**Probes / limits.** Focused tests contain genuinely ambiguous and answer-equivalent synthetic cases plus production Racket episodes. Public/private separation is tested. The helper is intentionally small and local; a shared adoption proposal is F1, not an unauthorized shared patch.

## D6 — Use portable runtime paths and preserve failed iterations

**Prior rationale / unknown.** The first test fixture found `workspace/` beside the selected generator execution file. The public loader may return a legacy staged location, while the portable runtime copies task workspaces to `ROOT/generators/TASK_ID`.

**Choice.** Resolve the root with the public helper, then use the documented task workspace path. Execute pinned native lambda rules with the available `strip_rule_wrapper` helper after checking the source hash. Do not modify shared runtime imports to work around the legacy `wrap_rule` dependency.

**Probes / limits.** Retain 47-pass/25-error portable results and the earlier 10-failure prototype run. Final portable tests pass 84/84 in a separately snapshotted runtime. The final handoff adds another environment and fresh full-packet extraction. Evidence remains source-bound; successful intermediate results are not relabelled as final results.

## D7 — Keep audit findings separate from the selected repair

**Choice.** Audit only the two immutable drawn targets, without editing them. Both have correct Racket labels but underdetermined generated lessons. A1 adds a plausible numeric color-order rival; A2 expands the instruction-codebook family to 4,096 constant D4 maps.

**Evidence / limits.** A1 is one exact default-generated lesson, checked with eight Racket evaluations. A2 examines 12 overlapping seed/band windows and reproduces one through the production sampler; its 56 actual Racket evaluations cover 28 unique inputs. These are bounded findings, not prevalence estimates or approval revocations. The proposed next steps are strengthened rival checks/demonstrations, with concrete witnesses supplied.

## D8 — Deliver a replayable delta and truthful solve records

Keep the immutable assignment, source-bound patch, reports, probes, complete final census, failed iterations and both solves in the builder-produced return ZIP. Omit only the redundant successful intermediate full census to meet the 25 MiB expanded budget, while retaining its hash/count/source summary. Preserve earlier exposure declarations and masked-query status. Do not inflate visible-example passes into hidden-query success or present authored notes as a captured model trace.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/28423cdf02cc/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
