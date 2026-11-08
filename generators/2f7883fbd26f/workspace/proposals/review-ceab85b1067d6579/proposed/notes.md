# Working notes: 2f7883fbd26f

## Review 2026-10-04

Baseline generator SHA-256: `e65b4498b5978ea83e559a08327d34824ef7bd38e4b1b3dd6b0e69d3f94cd15d`.
Final generator SHA-256: `d5b20c0ceb49913daaea833f90e3813c572ec4b71b5526af271a48b2b7b74039`.

The baseline battery failed five stages. Root causes included unbound rule identity, a non-enforcing self-check, advertised overrides that were ignored or clamped, permissive unknown keys, a declared `bg_color` control that did nothing, and selected/archival Racket text drift. The generator was replaced with an exact constructive grammar rather than retry-and-truncate placement.

Key decisions:

- Preserve the selected canonical rule: count all sliding 2 × 2 all-1 windows and emit a five-cell unary bar.
- Pin `RULE_HASH = "6de5b0b7a0a5"` and synchronize only the selected `racket_target.target_code` with canonical authority. Archival `raw_code` remains preserved.
- Honor the complete Cartesian product of exact controls: dimensions 9–12, target count 0–5, decoy count 1–4, isolated-one count 1–4, and isolated-two count 0–4.
- Declare the two strongest canonical-fitting rivals: counting qualifying color-1 components and counting exact isolated 2 × 2 color-1 components.
- Use overlap strips as decisive witnesses. The final three-slot schedule contains two overlap roles and one canonical-separated role so all two-demo windows and all three-pair query rotations are identifiable against both declared rivals.
- Retain canonical-scale 9 × 9 support in every difficulty band while extending size only to 12 × 12.

Final evidence:

- `checks/after-final-r2/`: all 12 battery stages green.
- `checks/task-tests-final-r2/`: 10/10 task-local tests passed.
- `checks/lesson-census-final-r2.json`: 300/300 lessons materialized, 900 unique inputs, 0 production ambiguities and 0/900 rotated ambiguities.
- `checks/lesson-window-probe-final-r2.json`: 450 cyclic windows and 1,350 rotations passed across all bands and schedule starts.
- `checks/lesson-census-final.json`: retained intermediate evidence showing why the earlier one-overlap/two-separated schedule was rejected (150/900 ambiguous rotations).

Limitations: these are finite checks against declared, canonical-fitting rivals; they do not prove universal rule identifiability. The grammar deliberately stays near the canonical palette and scale instead of exploring arbitrary colors or much larger canvases.
## Current reviewer considerations

Source SHA-256: `d5b20c0ceb49913daaea833f90e3813c572ec4b71b5526af271a48b2b7b74039`.

# Decisions: `2f7883fbd26f`

## D1 — Preserve the canonical rule

**Choice.** Keep the semantic rule unchanged: count every sliding all-1 2 × 2 window and encode the result as a five-cell unary bar.

**Rationale.** Canonical pairs and live Racket execution agreed; the baseline rule-smoke stage already passed. The defects were in generator contracts, teaching support, and selected-text synchronization, not in the transformation.

**Alternatives rejected.** Counting separated blocks or connected target objects would fit canonical examples but fail overlap strips. Changing the rule to that shortcut would encode a canonical ambiguity rather than teach through it.

**Probe/failure mode.** `checks/question-shortcut/counterexample.json` contains a 2 × 3 target strip with intended count 2, component count 1, and exact-square-component count 0.

## D2 — Replace retry/truncate placement with an exact constructive grammar

**Choice.** Construct separated slots, overlap strips, decoys, and isolated cells with explicit exclusion zones, then verify the exact observed counts before returning.

**Original rationale.** The baseline notes did not explain the probabilistic placement design; its rationale is therefore unknown.

**Why changed.** Baseline overrides were often rejected, clamped, or unobservable, and truncation/overlap could change requested counts. Exact construction makes every legal override jointly meaningful and deterministic.

**Alternatives rejected.** Increasing retry limits would leave probabilistic failures and weak provenance. Silently reducing counts would violate the exact override contract.

**Limit.** The constructor supports the declared Cartesian product only; it deliberately does not expose arbitrary placement coordinates.

## D3 — Keep the task domain near canonical scale and palette

**Choice.** Use dimensions 9–12 and exactly colors `{0,1,2}`. Keep substantial 9 × 9 support in easy, medium, and hard bands.

**Rationale.** This preserves canonical morphology while allowing moderate geometric variation. Color 1 remains semantically load-bearing, color 2 supplies structured decoys, and 0 remains background.

**Alternatives rejected.** Arbitrary recoloring conflicts with a rule that literally tests color 1. Much larger grids add combinatorial clutter without teaching a new rule distinction.

**Probe/failure mode.** The profile-floor gate initially exposed insufficient canonical-size support; dimension weights were adjusted before the final battery.

## D4 — Advertise only exact, observable controls

**Choice.** Declare six controls: `grid_h`, `grid_w`, `n_target_blocks`, `n_decoy_blocks`, `n_singleton_ones`, and `n_singleton_twos`. Reject unknown keys and malformed values.

**Rationale.** These are direct semantic or distribution controls and can be recovered from every output by `observe_overrides`.

**Alternatives rejected.** The baseline `bg_color` was removed because changing background would leave the fixed-color rule/domain incoherent. Layout names were not exposed as public overrides because schedule roles already carry the only teaching-critical layout distinction.

**Verification.** Boundary and joint-axis tests cover all declared ranges, and the final override stage passed.

## D5 — Declare the strongest canonical-fitting rivals

**Choice.** Add executable rivals for qualifying-component count and exact-isolated-2 × 2-component count, expose them through `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`, and bind both to an overlap witness.

**Rationale.** Both fit all 4 usable canonical pairs and represent natural object-centric ARC inductions. A semantic gate cannot assess teaching sufficiency without executable alternatives.

**Alternatives rejected.** A copied list of names in a test would drift from production declarations. The retained probe discovers mappings dynamically.

**Limit.** Passing finite named-rival checks is evidence, not a uniqueness proof over every imaginable program.

## D6 — Use `overlap, overlap, separated`, not `overlap, separated, separated`

**Initial choice and failure.** The first repaired schedule used one overlap witness and two separated examples. It made all 300 fixed-query lessons identifiable, but the live census found 150 ambiguous rotations out of 900 because holding out the single overlap pair left only separated demonstrations.

**Final choice.** Use two overlap roles and one separated role in each three-slot cycle. With `EXAMPLES_NEEDED = 2`, every consecutive demonstration pair and every held-out-pair rotation contains an overlap witness.

**Alternatives rejected.** Disabling rotation checks would hide a real assembly fragility. Increasing the demo count would spend context rather than fixing witness redundancy.

**Verification.** Final census: 0/900 ambiguous rotations. Exhaustive probe: 450/450 windows and 1,350/1,350 rotations refute both rivals.

## D7 — Make `self_check` and strict checks semantic

**Choice.** Recognize dimensions, exact palette, target-window grammar, separated decoy squares, isolated singleton counts, output range, and profile-specific structure. Add negative mutations that must be rejected.

**Rationale.** A generator-owned checker should characterize the returned task domain, not merely rectangularity.

**Alternatives rejected.** Comparing only to generation metadata cannot validate externally supplied or mutated grids.

**Limit.** The checker recognizes this generator grammar, not every lawful input on which the canonical Racket rule could execute.

## D8 — Synchronize selected authority text without changing semantics

**Choice.** Replace only selected `racket_target.target_code` with the exact canonical `program_solution`. Preserve archival `raw_code` as historical text.

**Rationale.** The authority-sync failure was textual divergence with execution parity. Exact selected-text equality removes ambiguity while retaining provenance.

**Alternatives rejected.** Rewriting canonical rows was unnecessary. Overwriting archival raw text would destroy provenance.

**Verification.** `checks/source-binding.json` shows exact selected/canonical equality and distinct preserved archival text; final authority sync and rule smoke passed.

## D9 — Add portable regression and schedule tooling

**Choice.** Add 10 task tests and `workspace/lesson_window_probe.py`, supporting both source and staged task-test layouts.

**Rationale.** The general 12-stage battery does not run task-local tests, and the shared census does not enumerate all cyclic starts. Future edits need both fast exact regressions and a schedule-wide semantic probe.

**Alternatives rejected.** Tests importing private `scripts` modules or guessing repository depth would not be portable in the staged runtime.

## D10 — Freeze and replay the exact final delta

**Choice.** Generate the same source patch shape used by the return builder, apply-check and apply it to a fresh extraction of the original packet, compare hashes, and rerun focused tests there.

**Verification.** Patch SHA `49633de4ce4cc20e489550bb781dc04f939f3c279bddc8b1eb8aec3a0548c4b2`; `git apply --check` 0; apply 0; fresh generator SHA matched; fresh tests 10/10.

## Residual limitations

The distribution fixes canonical colors and a compact size range; it does not test arbitrary palette permutations. Semantic evidence covers the two strongest object-count rivals and explicit grammar mutations, but no finite suite proves universal induction. Audit findings for the two independently assigned generators were documented but intentionally left unchanged.

## Review 2026-10-20

Pinned baseline generator SHA-256: `d5b20c0ceb49913daaea833f90e3813c572ec4b71b5526af271a48b2b7b74039`.
Final generator SHA-256: `2b1bfbcfb59638475bc152c8792ba04672d8b400f1689fc78176314f1369c353`.

The retained 2026-10-04 review and `counterexamples/current-shortcut` were used as leads only. A fresh baseline battery measured one current defect: `defect_lint` reported 177 strict-scalar violations while the other 11 stages were green. Declared integer overrides passed through coercing `draw_int`; replay keys also accepted booleans/floats/strings, and negative sample indices were accepted.

Current decisions:

- Preserve the canonical sliding-window rule, `RULE_HASH`, production schedule, distribution, and `VERSION = "2.0.0"`.
- Validate `seed` and `sample_index` as exact integers before scheduling/RNG use; require nonnegative sample indices.
- Route all six declared integer override axes through `draw_int_strict`.
- Keep new regressions in separate test files; the inherited root fixture remains byte-identical to the packet baseline.
- Retain the original-family parameter study as a separate proposed prototype: `window_size ∈ {2,3}` and `target_color ∈ {1,2}`, chosen once per episode, with canonical default `(2,1)` returning exact canonical Racket text.
- Rebind shortcut evidence and the exposed solve episode to the final generator hash; preserve the earlier solve under `checks/prior-solve/`.

Final evidence:

- `checks/final-battery/`: fresh final-source run, 12/12 battery stages green.
- `checks/final-task-tests/`: fresh final-source run, 18/18 portable tests passed.
- `checks/lesson-census-final.summary.json`: 300/300 lessons, 900 unique inputs, 0 production ambiguities, 0/900 ambiguous rotations.
- `checks/lesson-window-probe-final.json`: 450/450 cyclic windows and 1,350/1,350 rotations passed.
- `checks/parametric/window-rule/report.json`: 4 complete settings/episodes, 68 protected-Racket applications, exact canonical default, all alternative settings refuted by demonstrations.

Known limits remain finite named-rival coverage, controlled parametric fixtures, fixed semantic colors in production, and no universal proof of induction. No Racket authority text or canonical semantics changed in this review.
