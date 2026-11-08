# Working notes: 306adf8e4c54

## 2026-10-02 review `review-51d5ced7ad16a1b9`

Baseline source hash: `63731dd929e4736ac3c7038ecea4257386e5ae1ba9c2673c86ed9af6bacd847f`.
Final source hash: `2dc2a95dfa78e61a2e93c522a6f3ab914804e085fd2de974e383a392fe3cb419`.
Canonical rule hash: `aff0e8ed7bbb`.

The baseline generated valid active gaps but exposed dead and contradictory axes, had no rule hash or semantic contract, and avoided the counterexamples needed to distinguish the canonical one-pass literal-yellow rule. A 200-seed/four-example census found at least one surviving wrong rule in every lesson in all three bands.

Version 2.0.0 replaces the old surface with four scheduled semantic profiles: canonical morphology, chained gaps, negative controls, and a noncascade case. It declares eight rivals, causal witnesses, a Python mirror, exact override observation, lesson identifiability, and mutation fixtures. The final census has zero named rival survivors across 200 lessons per band. A regression test covers medium seed 115, where an intermediate non-yellow sandwich was accidentally crossed by an active yellow sandwich and therefore failed to distinguish arbitrary equal-color completion.

The Racket authority was not edited. Final isolated battery: 12/12 green. Task-local tests: 9/9 in both repository and portable runtime. Remaining limitation: named rivals and finite samples are not exhaustive, and the deterministic profile schedule may itself become learnable.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2dc2a95dfa78e61a2e93c522a6f3ab914804e085fd2de974e383a392fe3cb419`.

# Decisions for `306adf8e4c54`

## D1 — Preserve the canonical Racket authority

**Choice.** Leave canonical `program_solution`, selected `target_code`, and archival `raw_code` unchanged.

**Original rationale.** The original rule implementation was already correct on canonical examples and executable samples; the review evidence did not identify an authority defect.

**Alternatives considered.** Rewriting the Racket rule for style or adding iteration. Both were rejected: style-only authority churn adds risk, and iteration is semantically wrong for the task.

**Probe.** Baseline rule smoke already applied the rule 120 times without crash. Final rule smoke added Python mirror parity and matched 120/120 draws. Authority synchronization confirms all three sources share the same exact and normalized hashes.

**Failure mode / limitation.** Mirror parity is sample-based. It supports, but cannot mathematically prove, equivalence for every possible grid.

## D2 — Remove fake breadth instead of repairing nine misleading axes

**Choice.** Replace `grid_h`, `grid_w`, `palette_kind`, `n_gaps`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` with one exact axis: `scene_profile`.

### Baseline input choices

| Baseline choice | Original rationale | Measured problem | Decision |
|---|---|---|---|
| `grid_h`, `grid_w` | Presumably incidental shape diversity; no retained rationale beyond metadata. | Declared valid ranges exceeded difficulty-specific draw ranges, causing generation errors and override mismatches. | Encode four purposeful shapes in named profiles. |
| `n_gaps` | Presumably vary active work; no retained rationale. | Declared range and actual difficulty ranges disagreed; values became inert or invalid with negative textures. | Encode the needed counts in profiles and test lesson-level semantic coverage. |
| `palette_kind` / helpful `texture` | Original rationale unknown. | All four helpful values were byte-identical in sampled draws. | Remove rather than pretend color variation exists. |
| Degenerate `texture` values | Provide negative fixtures. | `no_pairs`, `no_gap`, and `gap_blocked` were advertised as ordinary valid inputs while failing ordinary self-check requirements. | Keep negative behavior only as explicit mutation fixtures, outside the training domain. |
| `palette_size`, `n_distinct_colors` | Original rationale unknown. | Singleton value 1; incapable of exercising an override effect. | Remove. |
| `position_bias`, `density` | Original rationale unknown. | Single unprobeable tokens, not real axes. | Remove. |

**Alternative considered.** Make all nine axes truly combinatorial. Rejected because most are incidental to this literal-color local rule and would greatly enlarge the contract without teaching the distinctions the model needs.

**Probe.** Baseline override matrix found 24,739 findings over 119,070 draws. The final matrix covers five exact cases over three bands, accepts 450/450 draws, rejects unknown keys, and reports no findings or warnings.

**Failure mode / limitation.** A single profile axis offers less free-form morphology than the baseline claimed. This is intentional: trustworthy narrow coverage is preferred to unobservable controls.

## D3 — Use a deterministic four-example semantic schedule

**Choice.** `sample_index % 4` schedules `canonical_7x7`, `chain_8x8`, `controls_9x9`, and `noncascade_8x9`; `EXAMPLES_NEEDED = 4`.

**Rationale.** A training lesson should teach the rule, not merely contain cells where the rule fires. The four profiles collectively refute all declared plausible shortcuts in every consecutive four-example window.

**Alternatives considered.** Randomly select profiles, weight rare controls, or rely on aggregate corpus coverage. Rejected because a random lesson can omit the decisive witness even when aggregate coverage looks healthy. A deterministic window gives a local guarantee.

**Probe.** `test_every_sliding_four_example_window_refutes_all_named_competitors` checks 16 sliding starts in each band. The larger source-hashed probe checks 200 lessons per band. Final result: zero lessons retain any of eight rivals.

**Failure mode / limitation.** A model may learn the four-position schedule or profile templates. Layout RNG, orientation changes, decoys, and four shapes reduce that risk, but the profile family should grow if future evidence finds a new shortcut.

## D4 — Choose controls by causal distinction

### `canonical_7x7`

**Choice.** Include horizontal and vertical active gaps plus an active gap adjacent to another yellow cell.

**Why.** This remains close to public canonical morphology while rejecting a rule that only fills isolated `4,0,4` triples.

**Rejected alternative.** Only isolated triples. Baseline lessons made `isolated_pairs_only` survive 200/200 in every band.

### `chain_8x8`

**Choice.** Include multiple active gaps on one line and a wider-distance aligned pair.

**Why.** Distinguishes “fill only the first gap” and “connect all aligned fours.”

**Rejected alternative.** Increase random `n_gaps` without a named relationship. Count variation alone does not ensure the relevant counterexample occurs.

### `controls_9x9`

**Choice.** Include a nonzero blocker between yellow endpoints, a zero between equal non-yellow endpoints, and long-distance aligned fours.

**Why.** Distinguishes zero-only behavior, literal color-4 specificity, and immediate-neighbor distance.

**Intermediate failure.** Medium seed 115 initially crossed the non-yellow sandwich with an active yellow sandwich. Both official and arbitrary-equal-color rules then wrote 4 at the midpoint, hiding the intended distinction.

**Fix.** `_analyze` counts a non-yellow sandwich only when its midpoint is not an active canonical gap; generation retries otherwise. The regression test was observed red before the fix and green after it.

### `noncascade_8x9`

**Choice.** Include a cell that would become eligible only after the first simultaneous fill.

**Why.** Separates a single read-from-original pass from iterative closure.

**Rejected alternative.** Explain simultaneity in metadata only. Metadata does not teach the visual input/output mapping.

## D5 — Declare competitors, witnesses, and lesson identifiability

**Choice.** Add eight named competitors: horizontal-only, vertical-only, any equal nonzero color, overwrite blocked midpoints, connect all aligned fours, isolated pairs only, first gap per line only, and iterative closure. Pair each with at least one causal witness and make `lesson_identifiable` report any survivor.

**Rationale.** This converts “semantic quality” into executable claims. A witness must not merely be present; it must cause the rival and official outputs to differ.

**Alternative considered.** Rely on `self_check` and morphology gates. Rejected because the baseline passed execution and morphology checks while every sampled four-example lesson remained ambiguous.

**Probe.** Final semantic gate: 8/8 witnesses firing, 8/8 rival claims verified, 12/12 sampled lessons identifiable. The larger 600-lesson probe finds no survivor.

**Failure mode / limitation.** The competitor list is not exhaustive. New model shortcuts should become new rivals and witnesses rather than prose-only warnings.

## D6 — Exact overrides and deterministic generation

**Choice.** Reject unknown values and keys, return fresh grids, avoid global RNG mutation, and expose realized override values through `observe_overrides`.

**Rationale.** Silent clamping and ignored controls create mislabeled training strata and make experiments irreproducible.

**Probe.** Task tests cover exact realization, invalid/unknown rejection, determinism, fresh allocations, and global RNG purity. Final override gate independently validates the declared surface.

**Failure mode / limitation.** Difficulty currently changes RNG context but not the profile schedule or shape names. Semantic coverage is intentionally equal across bands; future difficulty-specific additions must preserve the four-example identifiability guarantee.

## D7 — Keep the final repair small and authority-local

**Choice.** Change only the selected generator, its task-local tests, task notes, and summary. Add review probes as evidence; leave audit targets unchanged.

**Rationale.** The defect was in data generation and contract quality, not shared runtime code or canonical authority.

**Probe.** Return packaging rejects edits outside allowed paths. Final authority sync is green.
