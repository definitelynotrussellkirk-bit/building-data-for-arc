# Review 2026-10-25 — native chamber color-source family

Added a task-local native parametric family without changing production `generator.py` or the selected canonical authority. The exact default is `color_source=own`; the alternate `color_source=next` extracts room seeds in row-major room order, cyclically shifts the sequence left, and fills each room from the shifted color. Every parametric lesson has three or four rooms with distinct seed colors, so the source choice and shift direction are both visible from demonstrations.

The adapter supports 2–6 demonstrations and 1–4 private queries with stable count prefixes and matched inputs across settings. The four-query profile is 9×17, 15×19, 22×25 and 30×30; the largest 2×2 chamber layout retains more than 600 non-wall cells. A finite demonstration-only audit covers the declared alternate plus previous-room, reverse-order, fixed-seed and identity shortcuts.

Evidence: 136/136 task-local tests pass; native qualification covered both settings at seeds 0 and 17 with 32 protected-Racket evaluations; the source-bound `wrong_intermediate` witness was constructed and replayed through protected Racket. The witness shows that using the unshifted seed sequence produces a different final fill. This is bounded reviewer evidence only: owner acceptance and training admission remain pending.

# Working notes: 99f58784e7a0

## Baseline diagnosis

The selected `2.0.1` baseline was a narrow 2×2-only sampler with four always-distinct seed colors. Its public axis table advertised derived dimensions, singleton controls, palette aliases, and degenerate “textures” that were either ignored or produced malformed grids. It did not pin the canonical rule hash. Its `self_check` only looked for one full color-8 row and one full color-8 column, so it accepted all-background, singleton, short-line, no-seed, and multi-seed impostors.

Decisive retained evidence:

- `checks/before/checks/99f58784e7a0_before_lint.log`: missing `RULE_HASH`, singleton/unprobed controls.
- `checks/before-defect/checks/99f58784e7a0_before_defect_lint.log`: weak validator, four dead palette textures, degenerate-domain overlap.
- `checks/before-profile/checks/99f58784e7a0_before_profile_floor.json`: exact canonical-profile support was 27/60 overall and 0/20 in `hard`.
- `checks/before-semantic/checks/99f58784e7a0_before_semantic_gate.json`: no executable semantic contract.
- `checks/before-override/checks/99f58784e7a0_before_override_results.json`: unknown overrides accepted and 24,120 dimension-override mismatches, among other failures.

## Repair decisions

1. **Preserve the canonical rule and pin it.** `RULE_HASH = "5f0096488100"`; no Racket or canonical-data source changed.
2. **Replace nominal controls with three pixel-observable exact axes.** `layout_profile` has four canonical families, `scale` has canonical/expanded variants, and `color_pattern` has distinct/reused variants. All 4×2×2 combinations construct in every band.
3. **Cover the actual canonical morphology.** `_LAYOUT_SPANS` includes all five public pairs: vertical unequal, vertical equal, horizontal three-chamber, and 2×2 layouts, with exact canonical dimensions plus one-cell-expanded counterparts.
4. **Teach the hidden semantic distinction.** Public examples all use globally distinct chamber colors, so `distinct_colors_only` fits all five canonical pairs. Reused-color samples refute it without changing the true independent-chamber rule.
5. **Use a deterministic eight-profile curriculum.** Every three consecutive demonstrations contain a reused-color witness. Difficulty bands share complete support but use phase offsets `0/2/4`, avoiding byte-identical bands.
6. **Make malformed grids fail loudly.** The validator now requires complete outer borders, complete internal wall lines, only lawful wall cells, 2–4 chambers at least 2×2, exactly one seed per chamber, and at least one background cell per chamber.
7. **Require exact override observability.** Unknown axes and invalid values raise. `observe_overrides` recovers every declared axis from pixels, and generation asserts requested-versus-observed equality.

## TDD and intermediate failure

The initial task-local regression suite was run before replacement code and failed 90 tests (`checks/tdd-red.log`). The first complete repaired battery then found one remaining warning: easy/medium/hard were byte-identical (`checks/after-intermediate-dead-bands/`). A dedicated regression failed first (`checks/tdd-red-dead-bands.log`); a schedule-only phase shift fixed it without changing the domain or rule.

## Final measurements

All figures below bind to generator SHA-256 `90983480a07ba4d7f4881eeb29c8d13df7f0a9c70dabc365a354db7541e8c45a`.

- Final battery: 12/12 stages green, zero advisory/failed/interrupted (`checks/after/checks/99f58784e7a0_after_battery_summary.json`).
- Portable task suite: 99/99 passed (`checks/task-tests-final-2/result.json`).
- Independent curriculum probe: 768 generated inputs across three bands; zero validator failures or oracle mismatches; all 64 band/axis combinations and all 96 cyclic query rotations passed (`checks/curriculum-probe-final.json`).
- Source-bound census: 300/300 production lessons materialized, zero declared ambiguity/errors/warnings; 1,200 pair positions and 1,199 unique grids across bands (`checks/lesson-census-final.json`).
- Exposed post-repair solve: first revision passed 3/3 visible examples, with no reference consultation during solving (`solve/summary.json`).

## Remaining limits

The semantic evidence is finite. It eliminates the declared `distinct_colors_only` rival across the tested sampler and cyclic schedule, not every imaginable natural-language hypothesis. The production domain intentionally stays within four rectangular wall morphologies and two calibrated scales; arbitrary numbers of dividers, nonrectangular chambers, partial walls, and already-filled chambers remain outside the teaching grammar.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `90983480a07ba4d7f4881eeb29c8d13df7f0a9c70dabc365a354db7541e8c45a`.

# Decisions: 99f58784e7a0

## D1 — Keep the selected authority unchanged

**Original state.** The baseline did not declare `RULE_HASH`, but the selected canonical rule was already well-defined: complete color-8 walls delimit chambers; each chamber is filled with its lone seed color.

**Decision.** Pin `RULE_HASH = "5f0096488100"`, implement a pure Python mirror, and change only generator/task-local files. Do not alter the Racket rule or canonical examples.

**Why.** The observed failures were distribution, contract, validation, and control defects. Canonical execution itself was correct. Editing authority would create unnecessary review risk and could conflate a data-quality repair with a rule change.

**Alternatives considered.** Generalize the authority to partial walls or flood-fill around arbitrary color-8 components; modify canonical examples to include reused colors. Both were rejected because the task's selected authority and public data did not require a rule edit.

**Probe.** Canonical pairs are run through an independently written chamber oracle, the Python mirror, Racket smoke checks, and authority sync.

**Failure mode / limitation.** A historical archival bank copy remains divergent according to authority sync, but the selected source and executed rule agree. This return does not reconcile unrelated archival copies.

## D2 — Replace nominal axes with three exact pixel-observable axes

**Original rationale.** The baseline advertised dimensions, palette variants, singleton numeric controls, density, position bias, and texture. Most appeared inherited from a generic generator template rather than chosen from task semantics; the exact original rationale is unknown.

**Decision.** Expose only:

1. `layout_profile` — four wall morphologies;
2. `scale` — canonical or expanded;
3. `color_pattern` — globally distinct or reused chamber seed colors.

**Why.** Each value changes visible pixels and can be recovered without provenance metadata. The full 4×2×2 Cartesian product is lawful and constructive, making exact override behavior testable rather than aspirational.

**Alternatives considered.** Retain `grid_h`/`grid_w` as derived controls; expose arbitrary chamber counts and span vectors; keep palette aliases. Derived dimensions were rejected because many requested sizes cannot correspond to the named wall grammar. Arbitrary span vectors would greatly enlarge the contract without canonical evidence. Palette aliases were byte-dead.

**Probe.** `observe_overrides` reconstructs all three values. Tests enumerate all 16 combinations in four band modes (64 total) and generation asserts exact equality internally.

**Failure mode / limitation.** The API intentionally cannot request every rectangular dimension. It requests semantic morphology and scale, not unconstrained height/width.

## D3 — Model all canonical wall morphologies explicitly

**Original state.** Baseline output was always a 2×2 chamber grid with four distinct seeds. Canonical inputs include four morphology families and only 2–4 chambers.

**Decision.** Encode exact interior-span tuples for `vertical_unequal`, `vertical_equal`, `horizontal_three`, and `grid_2x2`, plus expanded variants that add one interior cell to each chamber side.

**Why.** This is the smallest family that gives exact support to every public pair and introduces controlled size variation without changing the underlying interpretation.

**Alternatives considered.** Sample arbitrary divider locations or arbitrary numbers of rows/columns. Rejected because they could produce unsupported one-chamber, five-plus-chamber, very thin, or visually alien tasks and make semantic review harder.

**Probe.** Canonical profile floor, independent span classifier, exact override tests, and 768-sample curriculum probe.

**Failure mode / limitation.** Nonrectangular rooms, partial dividers, nested walls, and more than four chambers are out of domain.

## D4 — Add repeated seed colors as the primary semantic witness

**Original state.** All five canonical pairs use distinct chamber colors. Therefore a rival that refuses to fill unless seed colors are globally unique fits every public pair.

**Decision.** Add `color_pattern=reused`, an executable `distinct_colors_only` rival, a reused-color witness, and declarations under `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.

**Why.** Reusing a color across separate chambers changes no true rule behavior but directly tests chamber independence. It is a high-value distinction that public examples cannot teach.

**Alternatives considered.** Use multiple seeds in one chamber, omit seeds, or partially prefill chambers. These would violate or complicate the selected input grammar rather than distinguish a lawful shortcut. Reuse is lawful and visually simple.

**Probe.** The rival fits 5/5 canonical pairs; independent and production implementations agree on a witness; all 300 census lessons and 96 cyclic rotations refute it.

**Failure mode / limitation.** Only one explicit plausible rival is declared. Other descriptions could remain extensionally consistent over this finite grammar.

## D5 — Use an eight-profile deterministic schedule with band phase shifts

**Original state.** Random baseline draws did not guarantee semantic teaching support, and hard samples had zero canonical-profile support in the 20-draw floor check.

**Decision.** Build an eight-entry cycle covering all layout/scale combinations and alternating distinct/reused color patterns. Set difficulty offsets to 0 (`None`/easy), 2 (medium), and 4 (hard).

**Why.** Alternation proves every three-demo window contains a reused-color witness. Canonical entries in the same cycle guarantee exact profile hits in all bands. Phase shifts preserve equal support while making the difficulty knob observable.

**Alternatives considered.** Independent random draws by band; changing chamber sizes more aggressively by difficulty; a four-entry schedule. Random draws cannot guarantee every lesson window. Strong band-specific domains would make some bands lose canonical support. Four entries cannot cover all eight layout/scale combinations.

**Probe.** Sliding-window tests, all cyclic query rotations, profile-floor battery, and the red-then-green dead-band regression.

**Failure mode / limitation.** “Difficulty” changes curriculum phase, not logical complexity. This is intentional because the rule itself has little natural difficulty scaling within the calibrated grammar.

## D6 — Make structural validation semantic, not cosmetic

**Original state.** `self_check` only required at least one full color-8 row and column. It accepted grids with no meaningful chamber rule.

**Decision.** Parse the complete wall arrangement and enforce values, rectangularity, complete outer borders, no stray wall cells, minimum chamber dimensions, 2–4 chambers, exactly one seed per chamber, and a nonidentity background cell in each chamber.

**Why.** A training validator must reject inputs for which labels are undefined, ambiguous, or trivial. Structural parsing also enables reliable axis observation and a pure rule mirror.

**Alternatives considered.** Add only seed-count checks to the old validator. Rejected because partial borders, stray wall fragments, tiny chambers, and malformed Python values would still pass.

**Probe.** Named destructive mutations, malformed inputs, defect lint, independent chamber analysis, and generated-sample stress.

**Failure mode / limitation.** The validator accepts lawful full-wall arrangements beyond the eight production profiles when they still have 2–4 chambers. `observe_overrides` intentionally returns no profile for such external-but-lawful inputs.

## D7 — Use independent test oracles and retain failures

**Decision.** Add `workspace/reference_probe.py` for an independent pixel-derived chamber oracle and `workspace/curriculum_probe.py` for deterministic support/identifiability stress. Keep initial 90-test failure evidence and the intermediate dead-band failure.

**Why.** A test that merely compares `rule_mirror` with helpers shared by generation can pass a coherent bug. Independent reconstruction makes the most important correctness checks noncircular. Retained failures demonstrate that regressions could actually detect the missing behavior.

**Alternatives considered.** Rely only on the shared battery or only on canonical examples. The battery did not discover task-local tests automatically, and canonical examples cannot refute the distinct-color shortcut.

**Probe.** Final portable task suite reports 99 passes; independent probe binds itself to both source hashes.

**Failure mode / limitation.** The independent oracle shares the written rule interpretation; it is not an independent human annotation source.

## D8 — Stop at a calibrated, evidence-backed expansion

**Decision.** Do not add arbitrary chamber counts, diagonal walls, noisy backgrounds, prefilled interiors, or multiple semantic rivals solely to maximize diversity.

**Why.** The repair's objective is trustworthy training data, not maximum combinatorics. Every added family should preserve a clear mapping to canonical semantics and receive exact validation/override coverage.

**Rejected alternative.** A generic connected-component flood-fill generator could create many more grids but would weaken the recognizable “full wall rows/columns partition rectangles” teaching signal and make strict-profile evidence less meaningful.

**Remaining limitation.** The resulting distribution is deliberately finite and structured. Future expansion should add one reviewed family at a time with a new adversarial rival and cyclic lesson test.


## 2026-10-23 reviewer delta: query-aware certificate and strict call scalars

Final source SHA-256: `ed331249ace21efd7958f88fd7054b171293ba1120201201dffe8d2f0d6ec17b` (incoming `90983480a07ba4d7f4881eeb29c8d13df7f0a9c70dabc365a354db7541e8c45a`); `VERSION` remains `3.0.0` and `RULE_HASH` remains `5f0096488100`.

### D9 — Classify competitors against the actual query

**Defect.** `lesson_identifiable` rejected a lesson whenever a declared rival fit all valid demonstrations, even when that rival produced the same output as the canonical rule on the supplied query. That made an answer-equivalent survivor look like query ambiguity.

**Decision.** Compute the canonical query answer and report a competitor only when it both fits every valid demonstration and changes that query answer. Keep malformed/wrong demonstration and malformed-query rejection unchanged.

**Regression.** `test_lesson_identifiable_only_flags_competitor_when_query_answer_changes` failed first on the answer-equivalent case, then passed for both answer-equivalent and answer-changing queries. The final semantic gate passed with rotation identifiability required.

### D10 — Validate public call scalars at the generator boundary

**Defect.** Focused defect-lint found 18 accepted invalid calls: boolean/float/string seeds and negative `sample_index` values. The schedule hook also accepted negative indices.

**Decision.** Require a literal integer seed and a literal nonnegative integer `sample_index` in `generate`; enforce the same index contract in `schedule_profile`. Negative integer seeds remain lawful to avoid changing behavior beyond the detected contract defect.

**Regression.** New parameterized tests failed before the fix and pass afterward. `checks/contract-adversarial-final.json` records 33 scalar cases: 18 invalid calls accepted by the incoming source and zero by the final source.

### Final scoped evidence

- Generated bytes are unchanged in 320 comparisons (256 default plus 64 exact-override cases), so the version remains stable and no new primary-task Racket replay was needed.
- Portable task suite: 112/112 passed (`checks/task-tests-release/result.json`).
- Focused lint, defect-lint, and rotation-required semantic gate passed (`checks/lint-release-2/`, `checks/defect-lint-release/`, `checks/semantic-gate-release/`).
- Remaining limit: the certificate checks the finite declared rival inventory, not every possible natural-language hypothesis.
