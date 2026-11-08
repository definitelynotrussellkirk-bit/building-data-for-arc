# Working notes: 22e428cda452

## Review review-9c7c174705bab8f4

Final generator version: `4.0.0`
Final source SHA-256: `b4655068a725dddba8295203ddfc360f896393209ba21c47b62d9010609ffd5a`
Canonical rule hash: `2e6c42d70b0f` (unchanged)

### Repaired

- Reject invalid scalar call arguments and overrides with exact type/range checks.
- Preserve official linked profiles while broadening legal dimensions and colors.
- Add a three-phase `top_only / bottom_only / mixed` schedule with three demonstrations.
- Add strict grammar, rule mirror, top/bottom witnesses, concrete `all_corners_square` and `all_corners_bent` rivals, and lesson-level identifiability.
- Synchronize the selected authority text exactly to canonical while retaining archival raw code.
- Retain minimal one-branch ambiguity counterexamples.
- Add an isolated two-setting `projection_inset` Racket/Python prototype.

### Verification

- Final strict battery: 12/12 green with required rotations and period enumeration.
- Random census: 300 lessons, 1,200 rotations, 922 unique inputs, 0 ambiguity.
- Period census: 9 lessons, 36 rotations, 14 unique inputs, 0 ambiguity.
- New focused tests: 10/10 pass through `workspace/run_focused_tests.py`, which stages the public portable runtime layout.

### Unresolved infrastructure blocker

The required portable aggregate task-test stage stops before collection because the frozen inherited fixture assumes a fixed parent-depth canonical path. Per assignment, it was not modified. See `WORK/checks/task-tests-final/result.json`. New tests were independently staged and executed; see `WORK/checks/focused-tests/`.

### Limits

The semantic claim is bounded to the two declared side-agnostic rivals and tested schedule/seed support. Exact overrides that cannot fit a scheduled branch may select a mixed mask. The parametric prototype is not wired into production and covers only inset values 1 and 2 on controlled 10×10 scenes.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. The twelve focused naming/writer checks passed across six tasks. This correction does not approve the prototype or rerun its full repair battery.
## Current reviewer considerations

Source SHA-256: `b4655068a725dddba8295203ddfc360f896393209ba21c47b62d9010609ffd5a`.

# Decisions: 22e428cda452

## D1 — Preserve the selected canonical rule

**Choice.** Keep rule hash `2e6c42d70b0f` and repair the sampler, validation, lesson contract, and selected authority text rather than changing transformation semantics.

**Why.** Canonical examples, rule smoke, and execution parity already agreed on the side-dependent corner projection. The baseline defects were contract and pedagogy defects, not evidence that the transformation was wrong.

**Alternative rejected.** Rewriting the Racket algorithm or changing shapes would introduce an unnecessary new rule family.

**Limit.** Python mirrors remain diagnostic; selected Racket execution remains authoritative.

## D2 — Use a three-phase lesson schedule

**Choice.** Cycle `top_only`, `bottom_only`, `mixed` by `sample_index % 3`, with `EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 3`.

**Why.** Three consecutive demonstrations then contain top and bottom witnesses under every cyclic start and every query holdout in the four-pair lesson window. This directly refutes the two shortest natural side-agnostic rules.

**Alternatives considered.** Pure random masks were broader globally but could cluster one branch within a lesson. A two-phase schedule had no dedicated mixed example and provided less compositional evidence.

**Probe.** All 9 fixed-seed band/start lessons and 36 rotations passed; 300 random lessons and 1,200 rotations also passed.

**Failure mode.** This proves only the declared period, sampled seeds, and named rivals. New rivals require new declarations/tests.

## D3 — Keep explicit override feasibility separate from default pedagogy

**Choice.** Exact overrides take precedence when the scheduled phase cannot realize them. In particular, `palette_size=3` or `4` may select a mixed mask even in a top-only/bottom-only phase.

**Why.** Rejecting a valid declared exact axis solely because of an incidental default schedule would make the override contract misleading.

**Alternative rejected.** Silently clamping palette size or accepting impossible combinations.

**Limit.** Lesson guarantees describe ordinary default draws; callers constructing override-heavy lessons must run the same lesson gate on their actual bundle.

## D4 — Declare only concrete executable lesson rivals

**Choice.** Add `all_corners_square` and `all_corners_bent` as pure deterministic rivals, with mapped top/bottom witnesses.

**Why.** Each has a minimal, reproducible one-branch counterexample and is a plausible compression of the visible rule.

**Alternative rejected.** A large speculative rival list without retained separating examples, which would create noisy or tautological gates.

**Probe.** `counterexamples/one_branch_rivals.json` stores selected-rule and rival query outputs for both directions.

## D5 — Synchronize only the selected authority field

**Choice.** Replace `racket_target.target_code` with the exact canonical `program_solution` through the sanctioned authority-sync workflow; preserve archival `raw_code`.

**Why.** Execution parity already passed, but a selected execution field should be byte-synchronized for provenance and reproducibility. Archival text is historical evidence, not the selected authority.

**Risk if wrong.** A mistaken field scope could erase historical evidence; the proposal and receipt show only the selected pointer changed.

## D6 — Keep the parametric variant isolated

**Choice.** Prototype `projection_inset ∈ {1,2}` under `workspace/parametric/` and do not wire it into production generation.

**Why.** It preserves object roles, colors, source erasure, and top/bottom glyph relationships while introducing one understandable episode-level parameter. Demonstrations distinguish both settings.

**Alternatives considered.** Varying glyph shape would alter the core reasoning pattern; varying per pair would make the episode inconsistent.

**Limits.** Only two settings and controlled 10×10 scenes were tested. No claim is made for larger insets, random layouts, or production training value.

## D7 — Do not patch the frozen inherited fixture

**Choice.** Retain the portable preflight failure and replay only the two new test files in an independently staged runtime.

**Why.** The assignment explicitly freezes `test_generator_22e428cda452.py`; changing it to obtain a green aggregate would falsify the review boundary.

**Consequence.** Completion is reported as blocked at the aggregate task-test gate even though the repair battery and 10 new tests pass.

## D8 — Treat the post-repair solve as exposed evidence

**Choice.** Declare `earlier_rule_exposure=yes` and `reference_consulted=no`.

**Why.** The solve was required after reviewing the generator and rule, so it cannot be represented as blind. During the solve lane, protected sources and private labels remained closed.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/22e428cda452/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D9 — Promote a projected-footprint finish with a source-count counterfactual

Assignment `review-0b61f0cebf027e32` adds a native contract separate from the
historical projection-inset prototype. The parameter is now
`finish = project_only | highlight_most_projected_color`. `project_only` uses
the byte-exact selected canonical source. The alternative first builds the
complete top-square/bottom-bent projection, then counts projected cells by
source color and recolors the unique largest-total color with 1.

The input-dependent intermediate is the projected grid plus the per-color
projected-cell totals. The retained `highlight_most_source_markers.rkt`
counterfactual substitutes source marker counts for projected footprint. The
first teaching pattern has three distinct colors: its top color has four
projected cells and wins, while the source-count tie-break selects a lower-valued
bottom color. The second pattern repeats the bottom color, making its combined
six-cell footprint win and refuting an always-top shortcut. A protected-Racket
witness changes seven final cells under the wrong intermediate.

The adapter independently supports 2–6 demonstrations and 1–4 queries, uses
matched inputs across settings, covers three- and four-marker scenes, and keeps
four queries including 30×30 all-corner stress. Across seeds 0 and 17, the
bounded audit exercised 12 setting/count jobs, 92 generated pairs, 93 protected
Racket labels, 20 matched-input comparisons, 24 prefix checks, and 12 large-case
jobs. Declared fixed-branch, numeric-color, order, all-color, and source-count
rivals had no surviving teaching set. This is finite evidence only.

Two inherited tests were repaired in this current assignment. One still searched
for obsolete `episode-*.json` public filenames after the owner had already moved
the writer to visible-content `challenge-<sha256>.json` names. The other used a
fixed parent-depth path for canonical data and failed only in the copied portable
runtime. The tests now assert the existing opaque-name contract and use
`reviewer_support.find_root()` plus `canonical_path()`. The final scoped
parametric suite passes 36 tests and the source-bound portable suite passes 48.
