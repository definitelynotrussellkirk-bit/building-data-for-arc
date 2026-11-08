# Working notes: f06d31332595

## 2026-10-02 review `review-2bebd44e54ddafa3`

Baseline generator SHA-256: `541e7478b17fd5e3faca3492baa07e9217f983456bfce9b2dee0c79de19489d2`.
Final generator SHA-256: `9bb48d51f27c434a2ebe10538eb5f6b7c0523be6db361406cc99cfc080566cb7`.
Canonical Racket rule hash: `2739381bfcfd` (unchanged).

The baseline battery finished 7 green, 2 advisory, 3 failed. The repair replaced the broad, partially inert override surface with exact `grid_h`, `panel_w`, `extra_right`, and `palette_size` observables; added strict validation; and introduced a deterministic three-example curriculum of canonical anchor, connected centered, and connected off-center examples.

The curriculum targets two executable rivals that fit every canonical pair:

- `grid_center_axis`: defeated by the off-center divider profile;
- `isolated_markers_only`: defeated by connected source motifs.

Task-local tests pass 12/12. The final 12-stage battery is all green. The semantic gate materialized 12/12 identifiable lessons, and the independent shortcut probe found no surviving rival in 36 cyclic lesson windows. See the root `REVIEW.md`, `DECISIONS.md`, and `QUESTION_ANSWER.md` in the packaged return for measured details and limitations.
## Current reviewer considerations

Source SHA-256: `9bb48d51f27c434a2ebe10538eb5f6b7c0523be6db361406cc99cfc080566cb7`.

# Design decisions for `f06d31332595`

Final generator SHA-256: `9bb48d51f27c434a2ebe10538eb5f6b7c0523be6db361406cc99cfc080566cb7`.

## D1 / R1 — Replace the broad axis list with four exact observables

**Decision.** Keep only `grid_h`, `panel_w`, `extra_right`, and `palette_size`.

**Rationale.** These values are visible in every generated input, have clear finite domains, can be recovered by `observe_overrides()`, and can be independently forced at both boundaries. They span scale, reflection distance, axis-versus-center ambiguity, and color diversity without pretending that fixed constants are meaningful axes.

**Original rationale.** The baseline appears to have aimed for broad combinatorial coverage through grid size, palette family, cell count, density, bias, color count, and texture. No stronger historical rationale was present in `notes.md` or associated evidence.

**Rejected alternatives.** I did not keep `position_bias=left_cells_with_divider` or `density=sparse` as one-valued axes; constants belong in invariants. I did not keep both `palette_size` and `n_distinct_colors`; one exact observable is sufficient. I did not keep `palette_kind` because named color pools are not semantically relevant to this color-preserving rule. I did not retain invalid degenerates on the normal `texture` axis because an advertised valid override should not systematically violate `self_check`.

**Probe and failure mode.** The before override report records mismatches, accepted unknown keys, self-check failures, and generated errors. The final override report covers 24,120 draws with no findings or warnings: `checks/after/checks/f06d31332595_after_override_results.json`.

## D2 / R2 — Preserve exact canonical-profile anchors

**Decision.** One of every three scheduled examples is a `canonical_anchor`. Its height, full width, and total number of colors exactly match one of the five canonical profiles. Its source marks remain isolated, as in the source demonstrations.

**Rationale.** Counterexamples alone could drift into a related but visually different family. Exact anchors keep the generated task recognizably grounded in canonical scale and sparsity while the other two profiles teach the missing distinctions.

**Rejected alternatives.** A loose canonical envelope was not enough: the baseline passed many envelope cases but had only 2/60 exact hits and none in hard. Copying canonical examples verbatim was also rejected because it would add no layout diversity and would risk memorization rather than family coverage.

**Probe and failure mode.** Final profile-floor evidence is 21/60 exact hits, split 9/20 easy, 8/20 medium, and 4/20 hard: `checks/after/checks/f06d31332595_after_profile_floor.json`.

## D3 / R2 — Offset anchor streams by difficulty

**Decision.** Difficulty changes the cyclic canonical-profile offset and the keyed layout stream.

**Rationale.** The first implementation made exact-profile anchors but produced duplicate anchor streams across easy, medium, and hard for the same seed/sample pair. A task-local test caught this after the larger repair was otherwise green. The implementation—not the test—was changed so each band remains canonical-scale but supplies a distinct curriculum.

**Rejected alternative.** I did not alter the canonical profile set or add arbitrary hard-only sizes merely to make bands different. The profile offset and layout key preserve source fidelity.

**Probe.** `repo/generators/f06d31332595/tests/test_generator_f06d31332595.py` checks canonical membership and distinct generation behavior; final result is 12/12 passed in `checks/f06d31332595_task_tests.log`.

## D4 / R4 — Schedule an off-center divider witness in every lesson

**Decision.** `connected_offcenter` adds one to three blank columns beyond the equal-width right mirror panel. The gray divider remains the transformation axis; the overall grid center no longer does.

**Rationale.** All five canonical grids place the divider at the geometric center, so `grid_center_axis` fits all 5/5 pairs. A guaranteed off-center profile is stronger than hoping random dimensions eventually expose the difference.

**Rejected alternatives.** Horizontal axes, movable guide colors, or asymmetric truncation were rejected because they either change the canonical grammar or complicate the rule. Random off-center frequency without lesson scheduling was rejected because aggregate witness counts do not guarantee that a complete three-example lesson disambiguates the rival.

**Probe.** The reusable `shortcut_probe.py` checks every declared canonical shortcut against every usable canonical pair and all 36 cyclic lesson windows. No window lets `grid_center_axis` survive. Evidence: `checks/f06d31332595_shortcut_probe.json`.

## D5 / R5 — Schedule a connected motif witness in every lesson

**Decision.** Both non-anchor profiles contain at least one orthogonally connected source pair, while retaining far-edge and divider-adjacent marks and more than one occupied row and column.

**Rationale.** The canonical source marks are isolated, so a rule that reflects singleton markers only fits every canonical pair. Connected motifs force the learner to treat every nonzero, non-gray source cell uniformly.

**Rejected alternatives.** Merely increasing density was rejected because accidental adjacency is not guaranteed and may be hard to diagnose. A single large solid block was rejected because it would introduce a separate “copy the object” shortcut. The chosen motif is a minimal connected witness embedded in otherwise varied marks.

**Probe.** The semantic gate observed connected witnesses in 406/600 draws and verified the named rival disagreement on 60/60 checked witnesses. All 36 cyclic lessons in the independent probe refute the rival.

## D6 — Use a deterministic three-profile lesson schedule

**Decision.** `sample_index % 3` yields `canonical_anchor`, `connected_centered`, then `connected_offcenter`; `EXAMPLES_NEEDED=3`.

**Rationale.** This gives each complete lesson source fidelity plus both required counterexamples. It makes the teaching contract inspectable, cheap to test exhaustively across cyclic starts, and stable under seeded generation.

**Rejected alternative.** Independent random profile selection could have a healthy corpus-level rate while still producing ambiguous lessons. The final reports therefore distinguish 600 individual draws from 36 overlapping cyclic windows and 12 independently materialized gate lessons.

## D7 — Realize `palette_size` exactly

**Decision.** Sample exactly 2–6 source colors and ensure every selected color appears. In connected profiles the adjacent pair shares one color, while the remaining marks realize the rest of the palette before repeats are added.

**Rationale.** The baseline declared both palette-size and distinct-color controls but painted each source cell from a pool, so neither request determined an observable count. Exact realization makes the axis testable and prevents metadata from overstating coverage.

**Rejected alternative.** A color-pool label was not retained because ARC color identity is arbitrary here; only distinctness and preservation matter.

## D8 — Strengthen recognition and failure behavior

**Decision.** Validate call arguments before generation; reject unknown overrides; require rectangular ARC-valued grids, exactly one full-height gray divider, source-panel width 3–8, blank right side, 0–3 extra right columns, 4–15 source marks, 2–6 source colors, and source spread across multiple rows and columns including the far edge.

**Rationale.** A generator's normal output domain and its validator must agree. Loud rejection makes tooling failures local and prevents invalid “degenerate” cases from polluting training.

**Rejected alternative.** I did not make no-divider, no-source, or prefilled-destination examples lawful. They do not have a unique intended action under this puzzle's rule and are better used as explicit negative probes outside the training distribution.

## D9 — Pin semantic rivals and lesson identifiability

**Decision.** Declare `grid_center_axis` and `isolated_markers_only` in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, witness mappings, and `LESSON_COMPETITORS`. Implement `lesson_identifiable()` against those competitors.

**Rationale.** A prose claim that examples are diverse is weaker than executable rival rules that are first shown to fit the canonical data and then shown to disagree on generated witnesses.

**Rejected alternative.** I did not enumerate an unbounded catalog of contrived rivals. These two are simple, canonical-compatible, query-changing, and directly tied to observable omissions in the source demonstrations.

## D10 — Leave the Racket authority unchanged

**Decision.** Do not edit the canonical puzzle row or Racket solution.

**Rationale.** The rule itself is coherent and passes canonical execution. The defect was in generation, overrides, and teaching coverage. Changing authority would create unnecessary review surface and risk redefining the task.

**Probe.** `rule_smoke`, `racket_lint`, and `authority_sync` all pass in the final 12-stage battery.

## D11 — Build reusable probes, not one-off claims

**Decision.** Add:

- `workspace/shortcut_probe.py`: discovers declared rivals from the generator, verifies 5/5 canonical fit, checks all 36 cyclic lesson windows, and retains exact disagreement grids.
- `workspace/audit_probes.py`: reproduces both assigned audit findings, validates the inputs, invokes Racket authority, and writes compact hash-bound JSON evidence.

**Rationale.** Future agents can rerun and extend the reasoning without reverse-engineering prose or copying a stale rival-name list.

## D12 — Test-first implementation history

The task-local suite was written before the production repair. After the main implementation, an intermediate test run still exposed duplicate cross-band anchors; production scheduling was corrected rather than weakening the assertion. The final suite passes 12/12. The final executable tests remain in the patch, while the decisive failed baseline battery and final battery evidence are preserved under `checks/`.
