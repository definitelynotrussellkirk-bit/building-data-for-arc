# Working notes: 85d01dd02c6d

## Current account — review-b854147a5b93c111

Generator version `2.1.0`; source SHA-256 `59feea64bf30cc0ae2c11b772914b6a4187ce705e3dc43df82aeb7bdc59e0260`; pinned canonical rule hash `071ab7615984`.

### Intended rule

Nonzero cells other than 9 are seeds. Each seed sees its own cell and extends in the four cardinal directions until a color-9 wall or the grid boundary. Wall cells remain 9. Every other cell becomes 8 exactly when at least two distinct seeds see it; otherwise it becomes 0.

### Defect and repair

Version 1.2.0 generated only an outer 9 frame, so ordinary lessons could not establish internal blocking. An intermediate full-divider repair still admitted the canonical-fitting shortcut “only complete divider rows/columns block rays.” Version 2.1.0 alternates canonical full dividers with contiguous three-cell wall segments. Every generated scene has a genuinely blocked aligned seed pair, a positive background overlap, and a threshold witness.

### Lesson policy

- three demonstrations (`EXAMPLES_NEEDED = 3`);
- declared schedule period 2: even indices full divider, odd indices partial segment;
- every three consecutive demonstrations and every one-pair query rotation over a four-pair window retains a partial-wall witness;
- declared rivals: ignore all walls, one seed suffices, and full-divider-walls-only.

### Validation boundary

`self_check` accepts the lawful canonical neighborhood, including canonical no-divider inputs and two-seed inputs. `_analyze` and `observe_overrides` enforce the stronger production grammar: exactly three distinct seeds and one recognized full-divider or three-cell-segment profile. Public exact axes are `grid_h`, `grid_w`, and `scene_profile`; invalid/unknown values fail loudly.

### Evidence

- focused tests: 100/100 passed;
- final battery: 12/12 green;
- strict semantic smoke: 12/12 identifiable, 0/48 ambiguous rotations;
- fixed-seed schedule enumeration: 6 lessons / 24 pairs / 24 rotations, zero ambiguity;
- broader census: 300 lessons / 1,200 pairs / 1,200 rotations, zero ambiguity or execution errors;
- authoritative short-wall counterexample: `counterexamples/partial-wall-shortcut.json` and `checks/counterexample-85d01dd02c6d/`.

### Known limits

The generator samples only full straight dividers and straight three-cell partial walls, not arbitrary wall shapes. Identifiability is checked against a finite declared rival set. Exhaustive schedule enumeration covers all period starts at one fixed schedule seed; the broader census samples but does not exhaust all seeds. No Racket authority behavior was changed.
## Current reviewer considerations

Source SHA-256: `59feea64bf30cc0ae2c11b772914b6a4187ce705e3dc43df82aeb7bdc59e0260`.

# Decisions for 85d01dd02c6d

## D1 — Preserve the canonical rule and authority

**Prior state/rationale:** The selected Racket rule already matched the canonical task and passed execution smoke checks. The defect was the generated input distribution, not output computation.

**Choice:** Keep rule hash `071ab7615984` and make no Racket or selected-authority edit. Add `RULE_HASH` to the generator and use an independent Python mirror only for focused tests and rivals.

**Alternatives rejected:** Changing the reference rule would hide a sampler defect; using the Python mirror as the production labeler would weaken independent authority checking.

**Probe/evidence:** final `rule_smoke`, `racket_lint`, and `authority_sync` stages in `checks/after-final/`; authoritative counterexample apply receipt in `checks/counterexample-85d01dd02c6d/racket.json`.

**Limit:** Mirror and tests can share a conceptual error; Racket replay and all canonical-pair tests reduce, but do not mathematically eliminate, that risk.

## D2 — Separate lawful-domain validation from production-curriculum validation

**Prior choice:** The first repair made `self_check` require a generated divider, three seeds, and all lesson witnesses. That was too narrow: at least one lawful canonical input has no internal divider, and canonical inputs may have only two seeds.

**Choice:** `self_check` now accepts the lawful task neighborhood: 9–11 by 11–13 rectangular grids, a full 9 border, two or three distinct non-8 seeds, and no interior-wall geometry except one straight row or column. `_analyze` enforces the stronger production contract—exactly three seeds, recognized full-divider/segment profile, blocker witness, threshold witness, and positive overlap.

**Alternatives rejected:** Keeping sampler policy inside `self_check` would falsely reject canonical-valid inputs; relaxing all checks would make distribution evidence non-probative.

**Probe/evidence:** canonical acceptance tests plus malformed-grid and broken-profile tests in `tests/test_generator.py`; final self-check, grammar, distribution, and defect-lint stages.

**Limit:** The lawful validator intentionally covers the canonical neighborhood rather than every grid on which the Racket program happens to execute.

## D3 — Use full dividers and short wall segments

**Prior choice:** Version 1.2.0 used only an outer frame. The first repair used internal full dividers, which refuted “ignore all walls” but introduced a stronger shortcut: “only complete divider lines block.”

**Choice:** Retain four canonical-style full-divider profiles and add two exact three-cell segment profiles. Each generated scene contains an aligned seed pair separated by the wall and another clear overlap.

**Alternatives rejected:** Full dividers alone leave the strongest canonical-fitting rival untouched; arbitrary wall noise would be harder to validate and less canonical; duplicating only canonical inputs would collapse diversity.

**Probe/evidence:** `counterexamples/internal-wall-shortcut.json`, `counterexamples/partial-wall-shortcut.json`, the Racket replay in `checks/counterexample-85d01dd02c6d/`, and final task tests.

**Limit:** Only straight three-cell partial walls are sampled. This is enough to establish cell-level blocking against the declared rival, but it does not cover arbitrary wall shapes.

## D4 — Alternate morphologies on a declared period-2 schedule

**Choice:** Even sample indices draw full dividers; odd indices draw short segments. Declare `EXAMPLES_NEEDED = 3`, `LESSON_SCHEDULE_PERIOD = 2`, and the two schedule roles.

**Rationale:** Independent random mixing can produce witness-free windows. Period 2 guarantees every three consecutive demonstrations and every three-of-four query rotation contains a partial-wall counterexample.

**Alternatives rejected:** A random Bernoulli mixture lacks a per-lesson guarantee; forcing every scene to use a segment would discard useful canonical morphology; four demonstrations are unnecessary once all period starts and rotations pass.

**Probe/evidence:** `checks/schedule-period-s0.*`, `checks/semantic-final/`, and `checks/lesson-census-final.*`.

**Limit:** The exhaustive receipt covers all declared period starts at fixed schedule seed 0. The broader 300-lesson census samples more seeds, but neither proves behavior for every integer seed.

## D5 — Keep only three exact public axes

**Choice:** Expose `grid_h` (9..11), `grid_w` (11..13), and `scene_profile` (six named profiles). All overrides are exact, observable through `observe_overrides`, and invalid/unknown values fail loudly.

**Alternatives rejected:** Exposing internal wall coordinates, seed positions, and colors would create a large compatibility matrix without a clear public use; silent coercion would make override evidence misleading.

**Probe/evidence:** exact override tests and the final override stage in `checks/after-final/`.

**Limit:** Exact axes produce lawful individual instances but do not by themselves guarantee a balanced multi-example lesson; the default schedule supplies that balance.

## D6 — Declare and test the actual semantic rivals

**Choice:** Declare three competitors: `ignore_internal_walls`, `one_seed_suffices`, and `full_divider_walls_only`. Bind named witnesses to the relevant rivals and make `lesson_identifiable` require demonstrations that refute all three plus contain a positive background overlap.

**Rationale:** The original retained audit identified the first rival; focused comparison found the threshold rival and then the stronger canonical-fitting full-divider-only rival. Declaring them lets the semantic gate test the same hypotheses used in the design.

**Alternatives rejected:** An unnamed prose claim cannot be checked across lesson rotations; a copied rival list in a probe can drift from the generator declarations.

**Probe/evidence:** strict semantic gate and both lesson censuses; canonical-fit and short-wall regression tests.

**Limit:** The rivals are finite. Another compact program may agree on the sampled distribution while differing elsewhere.

## D7 — Treat interrupted baseline and battery runs as evidence, not success

**Choice:** Preserve failures and interruptions, resume only source-bound checkpoints, and claim completion only from the finalized `checks/after-final/result.json` and battery summary.

**Rationale:** Several long controller invocations ended at the outer execution boundary after a stage had run. A missing final receipt is not a pass.

**Alternatives rejected:** Discarding failed iterations would erase useful debugging evidence; treating console output as a finalized battery would overclaim.

**Probe/evidence:** intermediate check directories plus the final 12/12 summary.

**Limit:** Resumed execution is operationally more complex than one uninterrupted command; feedback F1 proposes stronger atomic checkpointing.

## D8 — Leave adversarial audit targets unchanged

**Choice:** Report findings for `f891d1ff5dd8` and `959992fc8fa9` without editing either target.

**Rationale:** Audit is findings-only. The f891 issue is a concrete undeclared lesson rival; the 959 issues are independently reproducible intake failures, while its core repeated-color geometry branch appears intentional.

**Evidence:** `AUDIT.md` and `checks/audit/<task>/`.

**Limit:** These audit findings do not approve, repair, or close either target.

## D9 — Add the native `wall_scope` parametric family (current review)

**Choice:** Preserve the canonical default byte-for-byte as `wall_scope=every_wall`, and add the nearby `axis_dividers` setting. The alternative first classifies color-9 cells into an input-derived blocker mask containing only cells on complete rows or columns; the original ray-overlap computation then consumes that mask.

**Sequential dependency:** A classifies the episode's blockers; the intermediate is the coordinate set used by every line-of-sight test; B casts inclusive cardinal rays, counts visible seeds, preserves 9, and paints 8 at count at least two. A protected-Racket wrong-intermediate witness replaces the 58-cell axis-divider mask with the 67-cell all-wall mask and changes the final 12x14 output (`checks/85d01dd02c6d/causal/witness.json`).

**Lesson construction:** Inputs are matched across settings. Every scene contains a clear overlap pair, a pair blocked by a complete divider, and a pair separated by a short wall that distinguishes the settings. The first two demonstrations cover both orientations; supported counts are 2–6 demonstrations and 1–4 queries; the fourth query is a substantive 30x30 scene. Public projection strips settings, programs, and query answers, and sequential turns reveal one query without future-count hints.

**Source binding:** unchanged generator SHA-256 `59feea64bf30cc0ae2c11b772914b6a4187ce705e3dc43df82aeb7bdc59e0260`; exact canonical program SHA-256 `1b700549ad02b14ee862b6569346e5c10c75c2a29477c0d8f860747e17730045`; alternative program SHA-256 `dcc7066273418e6d7647cde0592f55fe3fa8ce81e21206611ea55f2db79c00be`; adapter SHA-256 `2db8a056624789eefcdc77986b369326bc6d327af9765ea9f49cd3f7a30551b1`; prototype SHA-256 `29ae9b419559249e1f7178fd13936d661743bd9d8efba22ab5d97fb0fffc45fd`.

**Evidence:** native qualification passed four jobs (both settings, seeds 0 and 17, three demonstrations and four queries); the focused 28-test suite and staged 128-test task suite passed; the protected-Racket finite-rival audit checked 24 labels with no surviving tested rival; public export validation passed; and a 128-seed boundary stress generated 1,024 episodes / 6,656 pairs with zero failures.

**Limits and next action:** The finite rival set is not a uniqueness proof, and only bounded seeds were exercised. Reviewer status is `ready`, not accepted. After integrating these exact bytes, the owner must rerun native qualification, replay the sequential witness, and perform fresh acceptance; no training activation is implied.
