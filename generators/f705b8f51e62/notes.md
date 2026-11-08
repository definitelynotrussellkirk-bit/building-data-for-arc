# Working notes: f705b8f51e62

## 2026-10-05 review: semantic curriculum and contract repair

The pinned baseline generator SHA-256 was `8e9ed8c11a247a9e9f770e6a414e43645728e0244fe0010c6c92ba254117089b`. Its canonical and generated examples were monochrome. Consequently, the plausible rule “crop any largest component” fit all three canonical pairs and ordinary generated data, even though the actual rule uses the defective component's color. The baseline also lacked `RULE_HASH`, advertised controls it did not honor, exposed singleton/unprobeable axes, had no executable rival/witness contract, and produced byte-identical difficulty bands.

The selected repair:

- pins `RULE_HASH = "4ad429046360"` and leaves the Racket authority unchanged;
- exposes only four exact observable axes (`profile`, `template_size`, `n_canon`, `missing`) and rejects unknown/invalid inputs;
- preserves frequent exact canonical-profile anchors;
- alternates canonical and contrast profiles, so every three consecutive demonstrations contains a defect-color transfer witness;
- declares and executes `crop_largest_component` as a canonical shortcut, semantic rival, and lesson competitor;
- supplies an independent oracle/probe in `workspace/reference_probe.py` rather than testing the implementation against itself;
- makes easy/medium/hard contrast defaults materially different while keeping exact overrides legal in every band.

The first full after battery found one retained defect: all difficulty bands were byte-identical (`checks/after/checks/f705b8f51e62_after_defect_lint.log`). Four new regressions failed before the fix and the final suite passed 72/72 (`checks/tdd-red-bands/`, `checks/tdd-green-bands/`). The final source-bound battery is 12/12 green (`checks/after-final/checks/f705b8f51e62_after_battery_summary.json`). The production census materialized 300/300 lessons and 1,200/1,200 unique inputs, with zero ambiguities in production order or any of 1,200 query rotations (`checks/lesson-census-final.json`).

Known limit: these are finite checks against one declared plausible rival. They do not prove that no other program can fit the lessons. The alternating profile schedule intentionally correlates sample index with witness type; that correlation is accepted because it guarantees lesson-level identifiability and all tested cyclic starts/rotations remain supported.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `88e26cc7e14793e327d3549d6203563cf25daec92ccce425f8a12f565611d85a`.

# Decisions for f705b8f51e62

## Scope and source authority

The assignment selected baseline generator SHA-256 `8e9ed8c11a247a9e9f770e6a414e43645728e0244fe0010c6c92ba254117089b` and canonical rule hash `4ad429046360`. I treated the canonical `program_solution` plus selected base `target_code` as authority because they are byte-identical and solve all canonical pairs. I did **not** change any Racket source. The archival base `raw_code` is textually different but execution-parity clean; the final authority-sync stage reports `SELECTED_SYNC_ARCHIVAL_DIVERGENT`, not a rule failure.

Alternative rejected: rewriting or “simplifying” the Racket rule. The selected authority already matched all canonical labels, and the observed defect was in supervision—not label execution.

## D1: Preserve canonical-profile anchors

Canonical inputs contain two complete four-cell copies and one three-cell defect, all in one color, on one of three source canvas dimensions. I retained frequent anchors with those linked dimensions, palette cardinality, copy count, template size, and missing-cell count. Shapes and placements remain freshly drawn.

Why: broad examples alone can drift from the task prior, while exact copied examples would reduce effective data. Fresh anchors preserve the canonical morphology without memorizing coordinates.

Rejected alternative: remove all monochrome examples. That would fix the shortcut but discard the actual source profile and teach an unnecessarily narrower “defect always has another color” rule.

## D2: Add a color-transfer contrast profile

The core baseline teaching defect was causal: every example was monochrome, so the output color could be taken from a full component. In `contrast`, the defective component has a distinct color while geometry is unchanged. The intended answer reconstructs the complete shape in that defect color; `crop_largest_component` therefore fails.

Why this witness: it changes exactly the unobserved causal variable while preserving component grammar. The independent `workspace/reference_probe.py` confirms the shortcut fits all canonical pairs and fails the contrast witness.

Rejected alternatives:

- Merely increase shape diversity: the shortcut would still fit.
- Add more monochrome demonstrations: more examples of the same confound strengthen the wrong rule.
- Encode a prose warning without an executable rival: not testable at lesson assembly.

## D3: Use an alternating two-profile schedule

`canonical` and `contrast` alternate with a seed-dependent phase. Every three consecutive demonstrations therefore contain at least one contrast witness, and any three-of-four query rotation still contains one. The production census covered every requested start residue modulo six and all 1,200 rotations without ambiguity.

Why: a deterministic bounded schedule gives a proof-like local guarantee that random frequency cannot provide. It also keeps approximately half the stream canonical-profile.

Trade-off: sample index now correlates with profile. I accepted that intentional correlation because the downstream unit is a short ordered lesson and guaranteed identifiability is more valuable than independent profile draws. Finite declared-rival checks do not rule out undeclared shortcuts.

## D4: Expose only exact observable controls

The final public axes are:

- `profile`: `canonical|contrast`;
- `template_size`: 4–9 cells;
- `n_canon`: two to four full copies;
- `missing`: one or two cells.

Every joint extreme tested is constructible and recovered by `observe_overrides`; unknown, mistyped, and out-of-range inputs fail closed. The baseline's palette, density, position, and color-count pseudo-controls were removed because they were dead, singleton, aliases, or not independently observable.

Rejected alternative: keep compatibility aliases. Silent or approximate controls are worse than a smaller honest interface for data generation and ablation.

## D5: Construct geometry rather than retrying loosely

Templates are connected random polyominoes; defects are enumerated connected strict normalized subsets. Broad examples use separated slots with a one-cell moat. Canonical anchors use a small exact backtracking packer because fixed source dimensions are tight. Every returned grid is checked against the grammar and requested observable signature before return.

Why: constructive generation makes extreme overrides reliable and prevents silent under-filling. A single universal backtracker was rejected as unnecessary cost for broad layouts; a single slot packer was rejected because exact source-sized anchors need tighter placement.

## D6: Make difficulty bands real but keep exact overrides global

The first complete after attempt exposed a dead-band defect: easy, medium, and hard were byte-identical. New red tests specified a progression for default contrast examples:

- easy: template 4–5, three or four complete copies, one missing cell;
- medium: template 5–7, two to four complete copies, one or two missing cells;
- hard: template 7–9, two or three complete copies, two missing cells.

Canonical anchors stay source-shaped, and an explicit override remains legal in every band. This separates curriculum defaults from the exact axis contract.

Rejected alternative: vary only canvas padding. That would silence the dead-band detector without creating a meaningful reasoning progression.

## D7: Test against an independent oracle

`workspace/reference_probe.py` implements components, normalization, intended output, the largest-component rival, signatures, and portable canonical loading without importing generator-private helpers. The task suite uses it for authority-adjacent behavior while also checking the generator's mirror against real Racket in the official rule-smoke stage.

Why: tests that reuse the implementation's own parser can reproduce the same bug. Racket remains label authority; the Python oracle is a regression aid, not a replacement authority.

## Verification and failed iterations

- The original before battery was interrupted after four completed stages; lint failed for missing `RULE_HASH` and two dishonest axes, while self-check, rule smoke, and defect lint were green. The morphology-only distribution stage passed separately and explicitly could not see semantic drift.
- Running the final 72-test suite against the immutable baseline produced 64 failures and 8 passes (`checks/tdd-red-baseline/`).
- The first repaired suite passed 68 tests, but the full battery found byte-identical difficulty bands. Four new tests failed (`checks/tdd-red-bands/`) and then all 72 passed (`checks/tdd-green-bands/`).
- Final source-bound battery: 12/12 green, no advisories or failures.
- Final portable task tests: 72/72 passed.
- Final census: 300/300 lessons, 1,200/1,200 unique inputs, zero production or rotation ambiguities against the declared rival.

## Remaining limitations and self-review

The schedule guards one high-value canonical-fitting shortcut, not all possible programs. The generated grammar also intentionally has exactly one defective component and all complete copies share one color; those restrictions match the selected authority/canonical evidence used here but are not a theorem about every conceivable extension of the task. The alternating witness profile introduces a predictable parity structure. I looked for a new shortcut caused by that restriction: arbitrary one-query rotations, all cyclic starts in the task tests, three bands, and exact extreme overrides remained identifiable, but an undeclared learner could still exploit correlations not represented by the rival set.
