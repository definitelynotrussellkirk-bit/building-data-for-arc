# Working notes: 5a85abd1e231

## Baseline inspected

The pinned selected baseline was v4.0.0 of the full canonical nine-tile compass generator. I used associated notes `GNOTE-004199` (full canonical grammar), `GNOTE-004201` (rejected partial-glyph shortcut), and `GNOTE-004200` (intended exact Racket sync) as leads only; measurements were repeated against the active bytes.

A complete before battery in `checks/before-complete/` passed 11 of 12 stages. `authority_sync` failed because task-local `raw_code`/`target_code` were behaviorally equivalent but not text-identical to canonical `program_solution`.

## Reproduced validation gap

The v4.0.0 analyzer mapped any valid-looking tile field with eight connected components to `touching_pair`. A 16×15 witness with two tiles at `(0,0)` and `(3,1)` creates a two-cell cardinal seam, still has eight components, and was accepted despite the declared one-cell contact grammar.

The regression was written and observed red before implementation. The repair records cardinal contact counts between every detected tile pair, accepts `touching_pair` only for exactly `[1]`, and accepts `separated` only for `[]`. Version is now 4.1.0.

## Authority repair

Both selected task-local Racket source fields were copied exactly from canonical `program_solution`; the algorithm and pinned rule hash are unchanged. Focused authority synchronization passed after the edit.

## Reusable probe

Run from the repository root or any directory:

```bash
python3 generators/5a85abd1e231/workspace/contact_topology_probe.py
```

It checks a separated sample, a lawful one-cell touching sample, and the historical two-cell seam, printing a JSON report and exiting nonzero on contract regression.

## Deliberate limits

No unsupported profiles, glyphs, palettes, transforms, or contact widths were added. The generator remains an exact canonical-profile teaching family. Declared-rival and finite lesson checks test known shortcuts; they do not prove universal induction.
## Current reviewer considerations

Source SHA-256: `619bb88b63a672d5df8d0b4fd80ef53b23c8443aaf9bdd3516e58484628dab58`.

# Decisions for `5a85abd1e231`

## R1 — Enforce strict public scalar types at the generator boundary

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and `sample_index >= 0`; reject booleans, floats, strings, and negative indices with `ValueError` before constructing the generation context.

**Original rationale.** The baseline implicitly relied on downstream context handling and had no explicit scalar contract. The current defect linter demonstrated that 33 malformed calls were accepted across easy, default, and hard probes, so the implicit behavior was not safe enough for reproducible data generation.

**Probe and evidence.** Eleven representative malformed calls were written as regressions and observed red in `checks/red-regressions/result.json`. The final portable suite passes them in `checks/task-tests-final/result.json`, and final `defect_lint` is green in `checks/after/checks/5a85abd1e231_after_battery_summary.json`.

**Alternatives rejected.** Coercing values with `int(...)` would merge distinct API requests and accept booleans. Leaving validation to `gen_ctx` preserved the reproduced failure. Validating only `sample_index` would leave malformed seeds non-replayable.

**Failure modes and limits.** This decision covers the public seed/index contract, not every override type. Existing exact-override validation remains responsible for task axes.

## R2 — Keep false heuristics as lesson competitors, not canonical shortcuts

**Choice.** Set `CANONICAL_SHORTCUTS` to an empty mapping and retain `reading_order_slots`, `color_order_slots`, and `first_signal_cell_slots` in `LESSON_COMPETITORS = SEMANTIC_RIVALS`.

**Original rationale.** The baseline intended these functions to represent plausible wrong rules that generated examples should refute, but aliased the same mapping into a canonical-equivalence declaration. The before semantic gate checked all three canonical pairs and found every declared shortcut mismatched all three.

**Probe and evidence.** The declaration regression failed before implementation in `checks/red-regressions/result.json`; the exact canonical mismatch evidence is in `checks/before/checks/5a85abd1e231_before_semantic_gate.log`. Final semantic checks and the 300-lesson census refute all three rivals.

**Alternatives rejected.** Rewriting the heuristics to imitate the canonical rule would destroy their adversarial value. Removing them entirely would weaken lesson diagnostics. Marking them canonical despite mismatches would preserve a false authority claim.

**Failure modes and limits.** An empty canonical shortcut set means no alternate rule is claimed equivalent. It does not assert that no true alternate implementation exists.

## R3 — Treat scene profile as presentation coverage, not a three-of-three semantic requirement

**Choice.** A three-demonstration lesson must include at least two distinct canonical profiles, both contact modes, correct Racket-equivalent labels, and a refuting example for every named competitor. It need not include all three presentation profiles when the fourth labelled pair is held out as query.

**Original rationale.** The v4.1 hook required all three profiles. A retained prior probe had 20 failures among 40 held-out rotations, and the current test-first reproduction failed query index 1 in easy, medium, and hard solely because one profile was held out. The object roles and glyph-to-compass relation remained fully represented.

**Probe and evidence.** `tests/test_review_repairs.py` holds out each of four scheduled pairs in every band. Red evidence is `checks/red-regressions/result.json`; final portable evidence is `checks/task-tests-final/result.json`. The wider source-bound census in `checks/lesson-census-final.summary.json` found 0 ambiguous production lessons among 300 and 0 ambiguous rotations among 1,200.

**Alternatives rejected.** Forcing duplicate profile examples into every four-pair lesson would require a larger or more rigid schedule without adding semantic information. Declaring rotations unsupported would be incompatible with downstream query shuffling. Dropping profile coverage entirely would permit unnecessarily narrow lessons.

**Failure modes and limits.** Two profiles are a task-specific judgment: profile changes canvas and palette presentation while the transformation is unchanged. The decision should not be generalized to tasks where profile selects rule semantics. Finite rivals and finite lessons do not prove uniqueness against every hypothesis.

## R4 — Preserve canonical authority and distribution geometry

**Choice.** Leave the canonical Racket program, `RULE_HASH = 2b7620b38386`, exact scene profiles, contact modes, and output construction unchanged. Version changes from 4.1.0 to 4.2.0 describe validation and curriculum-contract repairs only.

**Rationale.** All reproduced defects were in public input validation and metadata/lesson policy. Rule smoke and canonical outputs were already correct. A Racket edit would add risk without addressing the measured failures.

**Probe and evidence.** Final `authority_sync`, `rule_smoke`, and `racket_lint` stages are green in `checks/after/checks/5a85abd1e231_after_battery_summary.json`; the final exposed solve is bound to the same source hash in `solve/summary.json`.

**Alternative rejected.** Changing the Racket rule or canonical row was unjustified and would conflate a generator review with rule revision.

## R5 — Put all new tests in patchable files and restore the frozen fixture

**Choice.** Keep the baseline root `test_generator_5a85abd1e231.py` byte-identical to the packet baseline. Place repair regressions in `tests/test_review_repairs.py` and parameter tests in `tests/test_parametric_slot_rotation.py`.

**Rationale.** An early red run temporarily appended regressions to the frozen fixture. The packet contract explicitly reserves that fixture, so it was restored before final verification and the same behaviors were moved to new files.

**Probe and evidence.** `checks/task-tests-final/result.json` snapshots the final portable layout and reports 34 passed tests. The package diff contains no frozen-fixture change.

**Limit.** Retained early red output names the temporary fixture location; it is historical test-first evidence, not the final patch layout.

## P1 — Return a separate proposed compass-slot rotation family

**Choice.** Implement a runnable task-local prototype with one episode-level parameter, `slot_rotation_quarters ∈ {0,1,2,3}`. Decode the same directional glyphs and rotate only the destination compass slot. Keep setting 0 exactly canonical and keep all variant code outside the selected generator path.

**Original rationale.** The assignment prioritized a small original-family rule parameter. Slot rotation preserves object roles, glyph parsing, blank-tile behavior, and relational reasoning while changing a single interpretable rule choice. It is more substantive than a palette or canvas reskin.

**Probe and evidence.** `checks/parametric/5a85abd1e231-slot-rotation-v1/summary.json` binds four Racket texts, four retained seeds covering all settings, three canonical parity checks, complete public/private episodes, public redaction, and rival separation. The implementation and replay interface are in `workspace/parametric/`.

**Alternatives rejected.** Rotating the input canvas would be an augmentation rather than a rule parameter. Changing glyph shapes or colors would alter presentation only. Adding several parameters at once would make identifiability and attribution harder.

**Failure modes and limits.** This is **proposed**, not selected. Four episodes are bounded evidence, not distribution certification. Shared integration would need a formal variant authority and a reusable authoring harness before training admission.

## A1/A2 — Report peer defects without editing peer generators

**Choice.** Preserve both assigned audit sources exactly and return executable findings only.

**Rationale.** The audit lane requests adversarial evidence, not repairs. `c8d52f645999` has a validator/domain ambiguity and dead controls; `feaa89c467a0` has a generated class-count collision. Editing either would violate selected-task patch scope.

**Evidence.** See `AUDIT.md` and `checks/audit/<task>/` for source-bound reproducers and canonical Racket receipts.
