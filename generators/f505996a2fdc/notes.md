# Working notes: f505996a2fdc

## 2026-10-05 repair

Baseline generator SHA-256: `c7e8807a17391b92d1f23f604b0015614f5c435dc10f6323657e2cacd5e81ee9`.
Final generator SHA-256: `bcfa35e524539a52d02ba62a02c5abe00312e236f1c2620fb355085fcb3d680c`.
Canonical rule hash: `9bbe263d873a`; the Racket authority was not edited.

The baseline battery had five blocking failures: lint, self-check, defect lint, profile floor, and overrides. Inspection showed that several advertised axes were ignored, unknown overrides were accepted, no semantic contract or validator bound generation to the authority, and stochastic motifs could be empty or symmetry-degenerate.

The selected repair replaces the stochastic legacy grammar with an exact six-slot curriculum. It validates calls, uses only observable exact axes, includes all canonical input profiles in every band, permutes commands independently of morphology, and constructs colored motifs whose transforms are visible. It also declares executable rivals, witnesses, canonical shortcuts, and a leave-one-out lesson-identifiability hook.

Final evidence:

- after battery: 12/12 green in `checks/after-clean/checks/f505996a2fdc_after_battery_summary.json`;
- task-local tests: 18/18 pass in `checks/task-tests-portable/result.json`;
- source-bound lesson census: 300 lessons, 1,800 pairs, 1,800 query rotations, zero ambiguity/hook/scoring findings in `checks/lesson-census.json`;
- finite cyclic qualification: 1,152 six-pair windows and 6,912 rotations, zero errors in `checks/f505996a2fdc_qualification.json`.

Known limits: the motif bank is finite; all bands deliberately share canonical-scale support; the declared-rival checks are finite and cannot prove universal identifiability; the 300-lesson census contained 1,799 unique inputs among 1,800 labeled pairs. The post-repair visible-only solve passed 5/5 demonstrations, but the masked query label is intentionally unknown.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `bcfa35e524539a52d02ba62a02c5abe00312e236f1c2620fb355085fcb3d680c`.

# Decisions: f505996a2fdc repair

All measurements below refer to final generator SHA-256 `bcfa35e524539a52d02ba62a02c5abe00312e236f1c2620fb355085fcb3d680c` unless labeled baseline.

## D1 — expose only exact, observable input axes

**Input choice.** Keep `grid_h`, `grid_w`, `cmd`, `blob_h`, `blob_w`, and `n_colors`; remove legacy advertised axes that did not have an exact observable contract. Reject unknown names, booleans, strings, floats, and out-of-range integers.

**Original rationale.** No task-local notes justified the legacy texture, palette-kind, distinct-color, or density controls. They appeared to be generic diversity controls, but the baseline implementation either ignored them or allowed them to drift from the requested value.

**Alternatives considered.** (1) Preserve every legacy axis and implement all cross-products; (2) keep the names but document them as advisory; (3) narrow the public contract to rule-relevant observables. I selected (3). Implementing extra aesthetic axes would enlarge the state space without teaching a new rule branch, while advisory overrides violate the exact-control gate.

**Probes.** The baseline override stage failed. The final tests enumerate every axis boundary and all joint low/high combinations; the shared final override gate is green. `observe_overrides` provides an independent observable projection.

**Failure modes and limitations.** The generator offers less free-form texture variation than the baseline claimed. This is intentional: no unsupported promise remains. Future axes should be added only with exact observation and cross-product tests.

## D2 — use a six-slot lesson schedule with an independent command permutation

**Input choice.** Use six morphology slots, while assigning commands through a seed-stable permutation of `1..6`. Any six consecutive samples therefore contain all command meanings, independent of morphology.

**Original rationale.** The baseline sampled commands and object properties independently. That can produce lessons in which commands 5 and 6 never appear, even though the public canonical examples do not constrain either meaning.

**Alternatives considered.** (1) Pure random sampling with rejection until all commands appear; (2) force commands 5 and 6 only in fixed positions; (3) a cyclic schedule plus seed-level permutation. I selected (3): it has a finite proof surface, avoids unbounded rejection, and prevents a global fixed command-to-position cue.

**Probes.** The production census rotates every query in 300 six-pair lessons; all 1,800 rotations are identified against named rivals. The finite probe checks 1,152 cyclic windows and 6,912 rotations, with exactly 1,152 occurrences of each command.

**Failure modes and limitations.** This is a structured curriculum, not i.i.d. sampling. A learner could potentially notice six-sample periodicity. The command permutation is independent per seed/band family, and the downstream checks explicitly validate all query rotations, but they do not rule out every schedule-aware learner.

## D3 — prefer a small transform-sensitive mask catalog over unconstrained occupancy

**Input choice.** Construct a 2–4 by 2–4 tight object from audited masks, apply a legal orientation, then color occupied cells with 1–3 colors excluding the command. Require at least three body cells and a colored D4 orbit of at least four.

**Original rationale.** The baseline's Bernoulli occupancy was meant to create diversity. It also admitted empty bodies, accidental square/symmetric crops, and command outputs that could coincide, which damages semantic observability.

**Alternatives considered.** (1) Keep random occupancy and retry until valid; (2) grow connected random polyominoes procedurally; (3) use a small static mask bank with stochastic orientation/color. I selected (3) because all override cross-products are constructible, runtime is bounded, and the visible-transform property is easy to audit. Procedural growth would add complexity without a demonstrated teaching benefit.

**Probes.** Tests assert crop size, tightness, body count, command/color separation, reflection visibility, and authority outputs. The distribution gate and 300-lesson census found no malformed samples. The full census had 1,799 unique inputs out of 1,800, showing substantial but not perfect diversity.

**Failure modes and limitations.** Morphological support is finite and biased toward the catalog. A future expansion should add masks with explicit orbit/transform tests rather than return to unconstrained density sampling.

## D4 — declare executable rivals instead of relying on prose

**Input choice.** Declare four callable rivals: `swap_unseen_flips`, `unseen_as_identity`, `wrong_codebook`, and `ignore_command`. Declare exact witnesses and a `lesson_identifiable` hook that tests five-demo views against the query.

**Original rationale.** No prior semantic contract existed. Correct labels alone do not prevent a lesson from teaching a rival rule that fits every demonstration.

**Alternatives considered.** (1) Only mention risks in notes; (2) add fixed one-off witness grids; (3) make rivals and witnesses executable and bind them to generated lessons. I selected (3), retaining a standalone exact witness in `checks/f505996a2fdc_shortcut_witness.json` for human review.

**Probes.** Both canonical shortcuts fit 5/5 public pairs, proving they are genuine ambiguities rather than hypothetical names. The exact command-5 witness has independent Racket output, and every measured lesson/rotation refutes every declared competitor.

**Failure modes and limitations.** The set of rivals is not exhaustive. In particular, finite tests cannot certify universal induction or rule out a highly contrived schedule-dependent function.

## D5 — anchor canonical profiles in every difficulty band

**Input choice.** Five schedule slots exactly reproduce the five public `(grid height, grid width, total nonzero-palette size)` profiles; the sixth reuses a canonical canvas profile with a taller object. The same support exists in easy, medium, and hard.

**Original rationale.** The baseline had no dependable per-band canonical support and failed the profile-floor gate.

**Alternatives considered.** (1) Make bands progressively larger; (2) mix rare canonical-sized draws into each broad band; (3) keep every band entirely on the canonical scale. I selected (3). With only five public examples and a compact rule, a size-based difficulty distinction was not justified, and deterministic support is stronger than a low-probability floor.

**Probes.** Task tests compare generated schedule profiles against normalized canonical pairs in all three bands. The final shared profile-floor stage passes.

**Failure modes and limitations.** The `difficulty` label does not currently encode meaningful structural difficulty. It remains accepted for interface compatibility and RNG family separation. A future difficulty design should introduce semantic challenge without losing exact canonical support.

## D6 — preserve the selected Racket authority

**Input choice.** Bind `RULE_HASH = 9bbe263d873a`, implement a Python mirror for tests/semantic probes, and leave the canonical Racket row unchanged.

**Original rationale.** Rule smoke and authority sync were already green at baseline. The defects were in sampling, validation, and teaching, not the selected transform codebook.

**Alternatives considered.** Changing command meanings or modifying the Racket program was rejected because no authority defect was reproduced. The Python mirror is not used as production label authority.

**Probes.** Final rule smoke, Racket lint, and authority sync are green. The exact command-5 shortcut witness was run through supported `arcpuzzles apply`; its Racket output matches the Python mirror.

**Failure modes and limitations.** Mirror drift remains possible in future edits. `RULE_HASH`, codebook regressions, rule smoke, and the apply witness reduce that risk but do not replace the canonical authority.

## D7 — make regression evidence portable and reusable

**Input choice.** Put 18 tests under the selected task's `tests/` directory and add `workspace/qualification.py`. Resolve packet/repository roots with `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` rather than fixed parent depths.

**Original rationale.** The task had no selected tests or reusable cyclic-start probe. The first portable task-test run also warned that a fixed `__file__.parents[...]` path would be fragile.

**Alternatives considered.** A packet-root-only script was simpler but would fail in the portable runtime used by `task_tests`. A shared-tool modification was unnecessary for this task-local logic.

**Probes.** The final portable runtime reports 18 passed, 0 failed/errors/skipped. The qualification tool ran from the repository root and produced a source-bound JSON report with zero errors.

**Failure modes and limitations.** The qualification tool intentionally uses the Python mirror; its report must be paired with the Racket-backed census. Its finite defaults are a regression budget, not an exhaustive proof over all seeds.
