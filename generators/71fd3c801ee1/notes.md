# Working notes: 71fd3c801ee1

## Review repair — version 3.0.0

### Root cause

The imported generator and validator had drifted from the authoritative rule. They constructed and demanded identical-shape duplicates, while the Racket authority groups objects by the complete triple `(area, holes, symmetry class)`. The old declared axes also included ineffective or overlapping controls, unknown overrides were accepted, and the sampler missed the canonical 12×18 / six-color profile.

The baseline battery captured five failing stages (`lint`, `selfcheck`, `defect_lint`, `profile_floor`, and `override`) in `checks/before-complete/checks/71fd3c801ee1_before_battery_summary.json`.

### Repair

Version 3.0.0 uses a fixed canonical 12×18 layout with five separated, distinctly colored objects and a single exact observable axis, `target_family`. Each lesson contains:

1. two different outlines sharing one complete feature triple;
2. a unique object sharing area and holes with the target but differing in symmetry;
3. a unique object sharing area and symmetry with the target but differing in holes; and
4. a fifth control object with a different area.

Only the two complete-triple mates are recolored to `8`. This makes holes and symmetry independently necessary and directly refutes exact-shape, area-only, area+holes, and area+symmetry shortcuts.

Unknown overrides and unsupported difficulties now fail loudly. Generation is deterministic and does not mutate process-global randomness. `self_check`, `strict_canonical_like`, semantic rivals, witness fixtures, and lesson-identifiability hooks mirror the authoritative semantics.

### Verification

- Task-local TDD suite: 15 passed (`checks/task-tests-green-2-command.log`).
- Full after battery: 12 green, 0 advisory, 0 failed (`checks/after-final/checks/71fd3c801ee1_after_battery_summary.json`).
- Racket execution and authority synchronization are green; the authoritative rule source was not edited.
- Lesson census: 100/100/100 easy/medium/hard lessons materialized, 1,200 unique pair inputs, zero ambiguities/errors, and every declared rival refuted in every lesson (`checks/lesson-census-final.json`).
- Independent diagnostic tool and a concrete shortcut witness are in `workspace/`.

### Known limits

The census proves separation only for the finite declared rival set, not universal identifiability. Grid uniqueness is measured by exact normalized grid hashes rather than semantic equivalence. Approval and training-admission state remain outside the generator and were intentionally untouched.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `84c5209072ace3fc80b87f45b23a08ce7ec313992d7e320e0923b2e97e119b5e`.

# Decisions — 71fd3c801ee1

## D1: Treat the Racket rule as semantic authority

The authoritative transformation groups nonzero objects by the complete triple `(area, enclosed holes, reflection-symmetry class)` and recolors all members of repeated triples to `8`. I rejected the inherited “identical normalized shape” interpretation because it is only a sufficient condition for matching the triple, not the rule itself. The baseline canonical self-check failure and canonical rule hash `12f0cca6ed07` made that distinction executable rather than editorial.

## D2: Repair the curriculum, not only the validator

A validator-only patch would have made checks green while continuing to teach the wrong shortcut. Instead, every ordinary sample now contains different-outline equal-triple twins and two projection decoys. This makes each missing feature observable:

- exact-outline matching misses the target twins;
- area-only also recolors both one-feature decoys;
- area+holes also recolors the different-symmetry decoy; and
- area+symmetry also recolors the different-hole decoy.

The independent `workspace/feature_probe.py` reconstructs those facts without importing production code.

## D3: Use a constructive five-slot grammar

I chose five fixed non-touching regions inside the canonical 12×18 profile. This removes rejection-sampling failures and accidental object contact while preserving semantic variation by shuffling roles among slots, randomly choosing outlines, applying a shared flip, varying offsets, and sampling five distinct colors. A free-placement alternative was rejected because collision handling would add complexity without teaching additional rule content and had already contributed to profile drift.

The trade-off is explicit: the spatial envelope is narrower than the full abstract rule domain. Because roles are shuffled, no fixed slot identifies the answer, but the generator does not attempt arbitrary object counts or border contact.

## D4: Make only one axis public and observable

The old grid, palette, texture, and density controls overlapped or did not affect output reliably. The replacement declares only `target_family`, whose requested value is exactly recoverable from the repeated triple. Shape variant, color, flip, offset, and slot assignment remain deterministic internal randomness rather than pretending to be independently controllable axes.

Unknown overrides and unsupported difficulties fail loudly. This was preferred over silently ignoring knobs because the override matrix should test a real contract.

## D5: Match the retained profile exactly

The generator always produces 12×18 inputs with background plus five nonzero colors. This directly addresses the baseline profile-floor failure and keeps the repair comparable to the canonical demonstrations. I rejected variable dimensions/palette as a first repair because they were not necessary for semantics and made it easier to miss the retained profile entirely.

## D6: Separate canonical acceptance from production curriculum strictness

`self_check` and `strict_canonical_like` accept the documented canonical task manifold. Stronger properties that apply only to generated lessons—exactly one repeated pair, different outlines, and projection collisions—live in the private constructive check. An intermediate implementation incorrectly put those curriculum requirements in `strict_canonical_like`; the focused red test and first after-battery caught it before finalization.

## D7: Test first and retain failures

The task-local suite was authored before replacing production code. The initial source failed all 15 tests, establishing that the tests exercised missing behavior rather than merely describing the implementation. After the first repair, one new regression test failed because canonical examples were being over-rejected. Both red runs remain in `checks/`, followed by the final 15/15 green run.

## D8: Declare and census plausible rivals

The generator declares exact-shape, area-only, area+holes, and area+symmetry rivals. The three projection rivals are additionally declared as canonical shortcuts because each fits all three usable canonical pairs. The final lesson census evaluates the declarations rather than a copied external name list. Across 300 lessons, every rival is refuted in every lesson.

## D9: Preserve authority and approval boundaries

No Racket source, canonical row, archival solution, catalog approval, or training-safety field was edited. `rule_mirror` is a test oracle only; the selected Racket program remains authoritative. The final authority-sync and Racket-lint stages are green.

## D10: Build reusable review tooling

`workspace/feature_probe.py` is intentionally independent of `generator.py`. It accepts a grid JSON file, extracts 4-connected objects, computes area/holes/symmetry, applies the full rule and four rivals, and reports disagreements. The retained witness and report give future reviewers a small, deterministic semantic probe without coupling them to generator internals.

## Rejected alternatives

1. **Keep identical-shape duplicates and broaden `self_check`.** Rejected because lessons would still reward the shortcut.
2. **Random free placement with retries.** Rejected because it adds failure modes but no semantic coverage beyond role-shuffled safe slots.
3. **Retain all inherited axes.** Rejected because dead/overlapping controls caused the baseline override and defect-lint failures.
4. **Use only canonical demonstrations as regression tests.** Rejected because all canonical pairs are still compatible with area-only, area+holes, and area+symmetry shortcuts.
5. **Change the Racket rule to match the old generator.** Rejected because the selected authority was synchronized and the generator, not the rule, was defective.

## Known limitations and next useful extension

The finite rival set is not a proof of universal identifiability. Ordinary samples use exactly five separated monochrome objects, one repeated complete class, and a repeated-class multiplicity of two. A future version could schedule some lessons with a three-member repeated class or two repeated classes while retaining projection-decoy coverage across complete lesson windows. That extension was left out of this bounded repair because it changes the curriculum profile and would require a separate acceptance design rather than an untested “while here” expansion.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f029b9eb30ff87cf:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `84c5209072ace3fc80b87f45b23a08ce7ec313992d7e320e0923b2e97e119b5e`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/71fd3c801ee1/generator.py,unchanged SHA256 84c5209072ace3fc80b87f45b23a08ce7ec313992d7e320e0923b2e97e119b5e. No issue found within current84c52090 source finite audit:15 portable tests,3 canonical mirror labels,60 unique draws with strict/self checks clean;four declared rivals differ each draw and target_family controls observed. No owner rerun/new target approval. This does not replay the older d6385f3f/rule12f0 feature-triple counterexample. No owner audit rerun or new target approval. Target-local receipts: `checks/audit/71fd3c801ee1-task-tests.log` `checks/audit/71fd3c801ee1-task-tests.rc` `checks/audit/71fd3c801ee1/.task-tests.check.lock` `checks/audit/71fd3c801ee1/evidence.json` `checks/audit/71fd3c801ee1/probe.py` `checks/audit/71fd3c801ee1/probe.rc` `checks/audit/71fd3c801ee1/probe.stderr` `checks/audit/71fd3c801ee1/probe.stdout` `checks/audit/71fd3c801ee1/task-tests/checks/task_tests.xml` `checks/audit/71fd3c801ee1/task-tests/progress.log` `checks/audit/71fd3c801ee1/task-tests/result.json`

### Assessment or prior finding

## 71fd3c801ee1

**No issue found in the current source.** I checked generator SHA-256
`84c5209072ace3fc80b87f45b23a08ce7ec313992d7e320e0923b2e97e119b5e`
(version `3.0.0`, rule hash `f923d4259cc2`) rather than relying only on the
retained prior review.

The portable audit-phase task suite passed 15/15 tests at
`checks/audit/71fd3c801ee1/task-tests/result.json`. A separate source-bound
probe at `checks/audit/71fd3c801ee1/evidence.json` checked all three canonical
pairs and 60 generated samples (20 per difficulty band): all 60 inputs were
unique, every `self_check` and `strict_canonical_like` result was clean, all
four declared rivals differed from the selected rule on every sample, every
`target_family` request was observed exactly, and malformed difficulty or
unknown overrides were rejected. The canonical Python mirror matched all 3/3
labels. I also inspected the retained same-area shortcut evidence and current
review index; the present generator explicitly refutes that shortcut. This is
a finite check of declared rivals, not a proof against every possible
hypothesis.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
