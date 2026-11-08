# Working notes: `6d06c5b96c19`

## Intended rule

Column 0 is an instruction strip with exactly one red cell. Remove that column and rotate the payload rows **downward** by the red cell’s zero-based row index, with cyclic wraparound. Canonical authority and normalized rule hash remain `9b7b9cf11c40`.

## Final selected repair

- Generator version: `2.2.0`
- Final SHA-256: `691a8c0a81cfc305054e4b0fd6f71793d8983facceca0fcc5d08416e4185882c`
- Strict literal-integer validation for `seed`, `sample_index`, and integer overrides.
- Payload invariant is full cyclic row period; ordinary profiles keep distinct rows, while phase 2 has exactly one adjacent duplicate row to cover canonical support.
- Extra payload colors are connected dominoes rather than singleton accents.
- Broad odd phases use their bottom cue row; even canonical-size phases cover top, row 1, middle, and bottom.
- `four_row_instruction_code` is the canonical-fitting shortcut: rotate by cue row modulo four. Exact generated counterexample: `counterexamples/four-row-instruction-code.json`.

## Decision history

An initial broad-profile design used fixed cue row 4. The all-band window probe rejected it because row 4 is a half-turn on an 8-row medium grid, making up/down rotations identical. The final design uses each broad profile’s bottom row, which is decisive at all supported broad heights. Red and green evidence is retained under `checks/lesson-all-bands-*.log`.

A later semantic run rejected a witness name absent from `SEMANTIC_RIVALS`; the final source registers the same executable shortcut in semantic, canonical-shortcut, lesson-competitor, and bottom-witness declarations.

## Final measured evidence

- Battery: 12/12 green.
- Task tests: 22/22.
- Focused tests: 12/12.
- Source probe: 19 strict scalar rejections, 16/16 edge cases with exactly one singleton, 72/72 consecutive lesson windows, full row period in all scheduled phases.
- Lesson census: 300 lessons, 1,200 pairs, 0 production ambiguities, 0/1,200 rotated-query ambiguities, required rotation policy.

## Proposed parametric extension

`workspace/parametric/` proposes one episode-level parameter: `shift_direction in {down, up}`, default `down`. The down program is exact canonical authority; the up program changes only direction. Verification checks identical inputs across settings, 20/20 Racket/Python program-pair executions, six training disagreements, and two query disagreements. This prototype is not production-approved.

## Limits

Declared-rival and generic-search results are finite evidence, not a uniqueness proof. Broad bottom cues are an intentional curriculum restriction; exact overrides still support every legal cue row. Masked post-repair query labels are unavailable, so the solve records visible 3/3 only and makes no private-label claim.

## Current owner source and evidence limits

Accepted2.2.0 strict integer scalars,full-period payloads including scheduled duplicate rows,connected accent dominoes,valid executable modulo-four rival and decisive cue-row witnesses. Canonical Racket unchanged. Reviewer12/12 battery,22 task tests and12 focused regressions;300 ordered3-demo lessons/1200 required rotations clean. An earlier medium height8 half-turn ambiguity was repaired and72 all-band windows pass. shift_direction down/up prototype covers20 Racket/Python program-pair checks. Owner replaced ordinal setting-mapped public names and refreshed materialized gallery from actual passing Racket export tests;original sources/materialization retained. Finite rival limits,no production parameter API,variant approval,training admission or owner battery rerun.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d989bddd1e8298ce:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `61f93e42546ad0d631de47c29022f54855401ff6c907684d43d16177c7bfb3d3`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve the unique-row coverage hole:current2.2.0 schedule includes duplicate-row payloads while retaining decisive full-period cues;reviewer tests and300 lessons/1200 rotations are clean. Canonical unchanged;finite source-bound evidence.

### Assessment or prior finding

## 6d06c5b96c19

**Coverage hole: generated payload rows are always unique, but a canonical input contains duplicate rows.** The generator explicitly constructs pairwise-distinct staircase/binary-code payload rows to make cyclic shifts easy to observe. In 3,000 default draws (1,000 per band), zero inputs contained a duplicate payload row. Canonical pair index 1 contains the payload row `[4,4,1,5,5,5]` twice, and `self_check` accepts that canonical input.

A solver trained only on generated examples can use a unique-row lookup/set representation when matching input rows to output rows; that shortcut is never challenged and can collapse multiplicity or ordering when rows repeat. Add a low-rate repeated-row profile that retains at least one decisive nonperiodic row sequence, so the correct cyclic rotation remains identifiable without assuming row uniqueness.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d989bddd1e8298ce-v0001/audit_assets.json), manifest SHA-256 `49abf3f76f8792591a518796886623d2ebd7fbb2ea387a09d73666d44b4679c7`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `691a8c0a81cfc305054e4b0fd6f71793d8983facceca0fcc5d08416e4185882c`.

# Decisions — `6d06c5b96c19`

## D1: Reject coercive scalar inputs

**Decision.** `seed`, `sample_index`, and all declared integer overrides must have exact type `int`; booleans, floats, strings, and negative sample indices are rejected before generation.

**Why.** The baseline defect linter found 87 accepted invalid cases. Coercing values with `int(...)` made the public grammar and the executable behavior disagree. The final reusable probe checks 19 representative invalid scalar cases, and the final defect-lint/override stages are green.

**Evidence.** `checks/before/checks/6d06c5b96c19_before_defect_lint.log`, `checks/review-probes-final.json`, and `checks/after-handoff2/checks/6d06c5b96c19_after_defect_lint.log`.

## D2: Require full cyclic period, not universal pairwise uniqueness

**Decision.** Payload row sequences must have cyclic period equal to grid height. Ordinary phases keep distinct rows; phase 2 deliberately contains exactly one adjacent duplicate row.

**Why.** The canonical family contains a repeated payload row, but the old generator always emitted pairwise-distinct rows. That exposed a non-semantic training shortcut. Full cyclic period is the actual requirement for making every cyclic shift observable, so it permits the canonical pattern without making the intended shift ambiguous.

**Rejected alternative.** Merely removing the distinctness assertion would allow periodic payloads whose different shifts are observationally identical. Merely randomizing duplicate rows would make coverage non-deterministic and harder to audit.

**Evidence.** `checks/review-probes-final.json` records duplicate phase `[2]` in every band and full period in all scheduled phases.

## D3: Paint connected accent regions

**Decision.** Additional payload colors are introduced as vertical dominoes, including across the repeated row pair when applicable.

**Why.** Singleton accent cells created an accidental structural cue and caused marker-count mismatch diagnostics. Connected dominoes preserve exact palette support without introducing extra singleton candidates or destroying row observability.

**Rejected alternative.** Removing extra colors would narrow the declared 3..6-color domain. Scattering singleton accents would retain the defect.

**Evidence.** `checks/review-probes-final.json` reports exactly one singleton region—the red instruction marker—in all 16 edge-profile cases; final grammar and distribution stages are green.

## D4: Model the strongest canonical shortcut explicitly

**Decision.** Register `four_row_instruction_code`: remove column 0 and rotate downward by `red_row_index % 4`.

**Why.** All four canonical demonstrations use cue rows 0..3, so this rival fits every canonical pair while giving a plausible interpretation of the cue as a four-state instruction code. A bottom marker on a grid taller than four provides a lawful exact disagreement.

**Evidence.** `repo/generators/6d06c5b96c19/counterexamples/four-row-instruction-code.json` contains the exact generated input and both outputs. `checks/review-probes-final.json` records 4/4 canonical fits and a generated disagreement.

## D5: Interleave broad bottom-row witnesses

**Decision.** Every broad odd phase uses the bottom cue row; canonical-size even phases retain top, row 1, middle, and bottom roles.

**Why.** The first repair used a fixed broad row 4. The new all-band window probe showed that on height 8 this is a half-turn, so rotating up and down coincide and four medium-band windows remained ambiguous. The bottom row is direction-sensitive and exceeds the canonical four-row code for every supported broad height. Interleaving it means every consecutive three-example lesson has a decisive witness.

**Rejected alternatives.** Fixed row 4 fails at height 8. Random broad rows provide no deterministic guarantee for every lesson window. Expanding `EXAMPLES_NEEDED` would increase lesson cost instead of repairing coverage.

**Evidence.** Red: `checks/lesson-all-bands-red.log`. Green: `checks/lesson-all-bands-green.log`. Wider checks: 72 windows in `checks/review-probes-final.json` and 300 required-rotation lessons in `checks/lesson-census-final.summary.json`.

## D6: Keep rival registries semantically consistent

**Decision.** `four_row_instruction_code` appears in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and the bottom-marker witness declaration.

**Why.** An intermediate battery correctly rejected a witness rival that was not present in the semantic registry. The final organization makes the executable object identical across namespaces and lets both semantic checks and lesson checks evaluate it.

**Evidence.** Failing iteration: `checks/after-final/checks/6d06c5b96c19_after_semantic_gate.log`. Final pass: `checks/after-handoff2/checks/6d06c5b96c19_after_semantic_gate.json`.

## D7: Preserve canonical authority

**Decision.** Do not edit canonical examples, the Racket solution, `RULE_HASH`, catalog approval, or shared runtime interfaces.

**Why.** Every defect was in generator input validation, distribution, or declared-rival coverage. The intended transformation already matched canonical authority.

**Evidence.** Final `authority_sync` is green; the parametric verifier reports exact canonical text and normalized hash `9b7b9cf11c40`.

## D8: Keep direction variation as a separate proposed prototype

**Decision.** Add a task-local `shift_direction` prototype with bounded values `down` and `up`, canonical default `down`, selected once per episode.

**Why.** Direction is a small meaningful rule parameter that preserves the family’s instruction-column parsing and cyclic row-motion reasoning. Demonstrations distinguish settings before the query, and the same inputs are used for both settings.

**Rejected alternative.** Changing colors, dimensions, or cue positions alone would only vary sampling, not the executed rule. Wiring hidden direction into production would cross the packet’s authority boundary.

**Evidence.** `repo/generators/6d06c5b96c19/workspace/parametric/` and `checks/parametric-final-pass/verification.json`.

## D9: Leave reusable probes with the task

**Decision.** Keep `workspace/review_probe.py` and focused tests as future-agent tools.

**Why.** The failures depended on cross-band schedule windows, exact-type validation, cyclic-period properties, and canonical-fitting rival behavior. These are cheaper and more diagnostic as named deterministic probes than as repeated manual analysis.

## Known limits

The lesson census is finite and evaluates declared rivals plus the shared generic search set; it cannot prove that no other hypothesis exists. Broad-profile bottom cues are an intentional distribution restriction, balanced by canonical-size role coverage and full override support. The parametric extension checks two settings and one retained episode per setting; it is proposed evidence, not approval.
