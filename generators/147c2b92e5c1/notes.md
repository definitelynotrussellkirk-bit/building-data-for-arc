# Working notes: 147c2b92e5c1

## Current rule and source

The unchanged canonical rule reads the single code in row 0, selects the unique one-hole object among three separated monochrome body objects, crops it, applies the coded transform (`1` identity, `2` clockwise, `3` 180°, `4` counter-clockwise, `5` left-right, `6` up-down), then scales every cell to a 2×2 block. The selected generator is version `3.0.0`, pins `RULE_HASH = 93c771e66aca`, and has SHA-256 `658485dcaa05e19b78869e77afa0da15170000fbb0aa09a65a5f13fad82607a0`.

No Racket authority text changed. The active authority was already synchronized with canonical; an archival `raw_code` copy remains textually divergent but execution-equivalent, as reported by `checks/after-v2/checks/147c2b92e5c1_after_authority_sync.json`.

## Reversed decisions

- **Prior choice:** permissive copied controls (`texture`, inconsistent size controls, and unknown keys), with accepted overrides often ignored or impossible. **New choice:** six exact observable controls only: `grid_h`, `grid_w`, `transform_code`, `palette_profile`, `target_slot`, and `target_rank`; unknown, badly typed, and out-of-range values fail loudly. Evidence: the before override gate recorded 2,970 mismatches and 750 generation errors; the final override stage has no findings and rejects unknown keys.
- **Prior choice:** random transform sampling and shapes that could be invariant under the requested transform. **New choice:** a deterministic six-code schedule and a bank of asymmetric one-hole shapes whose six authority transforms are pairwise distinct. This directly closes retained audit `review-d3b87882f505f62c:v0001`, whose old-SHA seed-60 lesson admitted an always-identity rule.
- **Prior choice:** target position and size could remain accidental shortcuts. **New choice:** a four-profile schedule alternates left/right placement and largest/middle rank. Named selection rivals are executable and must be refuted by every four-demo/query rotation.
- **Prior choice:** default dimensions occupied a narrow slice while metadata advertised a wider range. **New choice:** a 20-slot size/palette schedule spans heights 9..15, widths 11..16, shared/distinct palettes, and places all five exact canonical profiles in every cyclic 20-draw window.
- **Prior choice:** acceptance-only validation. **New choice:** structural analysis requires a literal rectangular ARC grid, one code, blank separator, exactly three separated monochrome components, exactly one enclosed-hole target, two holeless distractors, and a transform-visible target.
- **Prior choice:** stale user-facing summary (five transforms and a fixed ring). **New choice:** `SUMMARY.md` and module `SUMMARY` describe the actual six-transform asymmetric curriculum.

## Lesson policy and evidence

Production lessons use four demonstrations and one query. The five consecutive samples may be rotated arbitrarily: task-local tests exhaust all 60 schedule starts, all five query positions, three bands, and seeds 0 and 60 against the ten declared transform/selection rivals. The reusable probe in `workspace/probe_lesson_schedule.py` reports 360 lessons and 1,800 rotations with zero ambiguity; the authority-backed wider census materialized 300 lessons / 1,500 pairs / 1,500 rotations with zero materialization, scoring, or declared-rival ambiguity errors.

The retained seed-60 case now has codes `[1, 2, 3, 4, 5]`; the always-identity rival disagrees with four of the five oracle outputs. Compact evidence is in `counterexamples/identity-shortcut-seed60-fixed.json`, while the old audit artifacts remain preserved under `counterexamples/review-d3b87882f505f62c-v0001/`.

## Verification

- Before battery on old SHA `869c76ad...`: 6 green, 2 advisory, 4 failed (`lint`, `selfcheck`, `defect_lint`, `override`).
- Final battery on SHA `658485dc...`: 12/12 green in `checks/after-v2/`.
- Portable focused tests: 18/18 passed in `checks/task-tests/`.
- Lesson census: 300/300 lessons materialized, 1,500/1,500 query rotations checked, zero declared-rival ambiguity in `checks/lesson-census-final.json`.
- Exposed post-repair solve: first revision passed all four visible demonstrations; query labels remained withheld.

## Known limits and open findings

The generator deliberately covers one structured scene family rather than every input on which the canonical program might execute. Identifiability results are finite and only against the ten declared plausible rivals; they are not a proof of unique induction among all programs. The historical audit entry remains preserved in `evidence/review_index.json` and is bound to the old source SHA; the current-source regression and schedule evidence address that exact shortcut, but catalog approval remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `658485dcaa05e19b78869e77afa0da15170000fbb0aa09a65a5f13fad82607a0`.

# Decisions — 147c2b92e5c1

## D1 — Preserve the canonical Racket rule

**Decision.** Keep the canonical transform/select/scale program unchanged and pin `RULE_HASH = 93c771e66aca` in the generator.

**Why.** Canonical examples, rule smoke, Racket lint, and execution parity were already sound. The defects were in lesson construction, metadata, and validation, not in the authority.

**Rejected alternative.** Editing Racket to accommodate the old sampler would silently change the task rather than repair its training distribution.

**Evidence.** Final battery `rule_smoke`, `racket_lint`, and `authority_sync` are green in `checks/after-v2/`; the final authority-set hash equals the before run's hash.

## D2 — Replace generic controls with six strict observable axes

**Decision.** Retain only `grid_h`, `grid_w`, `transform_code`, `palette_profile`, `target_slot`, and `target_rank`, with literal type/range validation and exact pixel observations.

**Original choice.** Metadata advertised controls such as generic textures and sizes that were inert, aliases, or incompatible with the actual layout. Unknown keys were accepted.

**Rejected alternatives.** Keeping legacy aliases would preserve silent no-ops; coercing booleans/strings/floats would make experiment provenance unreliable.

**Failure mode and probe.** The before override report recorded 2,970 mismatches and 750 generation errors, including requested heights/widths that could not be realized. Final override evidence reports PASS, no findings, and unknown-key rejection.

## D3 — Make all six transform codes visibly consequential

**Decision.** Use asymmetric one-hole shapes for which identity, both quarter-turns, 180°, and both flips produce six distinct tight crops; cycle codes 1..6 deterministically.

**Original choice.** A retained production lesson at easy seed 60 had codes `[6,1,1,1,1]`; the code-6 shape was vertically symmetric, so an always-identity rule fit all five labelled pairs.

**Rejected alternatives.** Merely balancing code frequency would not help when shapes are transform-invariant. Merely rejecting seed 60 would hide one symptom without enforcing the property.

**Evidence.** `test_retained_seed60_identity_shortcut_is_constructively_refuted`, `test_every_generated_target_exposes_all_six_transforms`, and `counterexamples/identity-shortcut-seed60-fixed.json`.

## D4 — Schedule position, rank, size, and palette witnesses

**Decision.** Combine a four-profile target-slot/rank schedule with a 20-profile size/palette schedule. The latter spans every advertised height and width and inserts all five exact canonical profiles in every cyclic 20-draw window.

**Why.** Random support does not guarantee that a complete four-demo lesson contains a witness against fixed-position, fixed-size, or fixed-transform shortcuts.

**Rejected alternatives.** Pure IID sampling could still produce locally ambiguous lessons. A narrow canonical-only schedule would improve profile-floor scores while under-covering advertised support.

**Evidence.** The task tests exhaust the 60-step least-common-multiple cycle, and the final defect/profile/diversity gates are green. The authority-backed 300-lesson census found zero ambiguity against declared rivals.

## D5 — Validate structure, not mere executability

**Decision.** `self_check` and `strict_canonical_like` inspect the code row, separator, component count, monochromaticity, connectivity, hole counts, and transform visibility. Canonical pairs remain accepted.

**Why.** The prior acceptance-only check could certify malformed or unteachable scenes, so downstream distribution results did not establish domain quality.

**Rejected alternative.** Checking only whether the Python/Racket rule returned a grid would validate labels, not the intended input grammar.

**Evidence.** Focused destructive-mutation/impostor tests and the final self-check/grammar stages.

## D6 — Make shortcut claims executable and finite

**Decision.** Declare six fixed-transform rivals and four wrong-selection rivals, map witnesses to them, and reject any lesson where a rival fits all four demonstrations but differs on the held-out query.

**Why.** Individual witness frequencies do not prove that each assembled lesson teaches the rule.

**Limit.** These ten rivals are plausible and reproducible but not exhaustive. Reports therefore say “no ambiguity found against declared rivals,” never “unique rule proven.”

## D7 — Keep a reusable schedule probe

**Decision.** Add `workspace/probe_lesson_schedule.py`, which loads the exact selected source via `reviewer_support`, enumerates the finite schedule, rotates every query, and iterates the generator's actual rival declarations.

**Why.** Future edits can cheaply reproduce the retained failure class before running the more expensive Racket-backed census.

**Scope.** Its labels come from the Python mirror; authority claims remain bound to the final battery and lesson census.
