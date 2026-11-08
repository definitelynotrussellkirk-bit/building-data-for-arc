# Working notes: 0f423424b1dc

## Review outcome (2026-10-03)

Final selected generator SHA-256: `bc41dfd17675af9b71ba310882da7d02dd02894c80c2b7948eaec2be0160c85d`.
Canonical Racket authority was not changed. The generator now pins `RULE_HASH = "1e2581a2f271"` and an independent rule-smoke/authority battery confirms parity.

### Baseline defects

The imported `1.2.0` generator produced only matching endpoint columns. Its metadata advertised several controls that were decorative or collapsed: `palette_size` had a singleton domain, `position_bias` had one unprobed value, all four helpful textures were byte-identical to ordinary generation, and degenerate negative fixtures overlapped the ordinary texture domain. It also had no rule-hash pin and no lesson-level contract showing that the canonical positives distinguish the actual rule from plausible rivals. Retained evidence is under `checks/before-*` and `checks/before-full-interrupted.log`.

### Selected repair

- Replace the decorative control surface with seven exact observable axes: `grid_h`, `grid_w`, `n_targets`, `n_mismatched`, `n_blocked`, `n_singletons`, and `edge_anchor`.
- Schedule four profiles by `sample_index mod 4`: canonical, mismatch, blocked, singleton.
- Keep 20% or more canonical-shaped support while using the other profiles as lawful teaching negatives.
- Declare executable semantic rivals and witnesses instead of relying on prose names.
- Require a four-demonstration lesson to refute all declared rivals through `lesson_identifiable`.
- Add `observe_overrides`, stronger structural validation, an independent Python rule mirror, exact override tests, and source-bound curriculum probing.

### Tests and measurements

Focused test development retained a failing red run (`checks/tdd-red.log`: 17 failures, 2 passes) before implementation and a green run (`checks/tdd-green-attempt1.log`: 19 passes). The final full task-local test command is recorded in `RESULTS.json`.

The complete after battery passed all 12 stages. Its summary is `checks/after/checks/0f423424b1dc_after_battery_summary.json`. The semantic gate sampled 600 final-source draws: 142/600 (23.7%) were strict canonical support, all declared witnesses occurred in every difficulty band, all three rival claims were independently checked on 60 sampled claims each, and 12/12 Racket-materialized lessons were identifiable.

The complete repository collection was also exercised. Two monolithic invocations exceeded the outer execution limit after >91% progress; all 28 collected test files were then partitioned into four fresh-process groups, totaling 203 passed, 34 Racket-dependent skipped, and 0 failed across 237 tests (`checks/final-repo-groups-summary.json`).

`workspace/lesson_probe.py` inspected 100 disjoint five-pair lessons per band, bound to the final generator SHA. For each of easy/medium/hard: 100/100 lessons were identifiable, 500/500 inputs and outputs were unique, all four cyclic starts appeared 25 times, each profile appeared 125 times, and each rival was refuted by the four demonstrations in 100/100 lessons. This is sampled evidence over the stated sampler, not universal induction.

### Known limits

The selected domain intentionally stays column-independent, with 6..12 rows/columns, 1..3 target columns, and at most one distractor of each declared type. It does not attempt dense scenes, multiple blockers of one type, adjacent endpoints, or interacting columns. The long lesson probe uses `rule_mirror` for throughput; independent Racket parity is supplied separately by rule-smoke, semantic-gate, authority-sync, and the exact shortcut counterexample.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `bc41dfd17675af9b71ba310882da7d02dd02894c80c2b7948eaec2be0160c85d`.

# Decisions: 0f423424b1dc

All final measurements below bind to generator SHA `bc41dfd17675af9b71ba310882da7d02dd02894c80c2b7948eaec2be0160c85d`.

## D1 — Keep the canonical Racket rule unchanged

**Choice.** Repair only the input distribution and its semantic contract; pin `RULE_HASH = "1e2581a2f271"`.

**Rationale.** The baseline rule-smoke passed and the canonical examples were consistent with the selected authority. The observed defects were generator-side: metadata, exact controls, and teaching coverage.

**Alternatives rejected.** Rewriting the rule would have increased authority risk without solving the curriculum defect. Treating the archival divergent source as selected was also rejected; final authority-sync reports selected parity and archival divergence explicitly.

**Probe/failure mode.** Full after `rule_smoke`, `racket_lint`, and `authority_sync` passed. A future authority hash change must force a fresh review rather than silently accepting this pin.

## D2 — Replace nine decorative axes with seven exact observable controls

**Choice.** Public axes are `grid_h`, `grid_w`, `n_targets`, `n_mismatched`, `n_blocked`, `n_singletons`, and `edge_anchor`.

**Rationale.** Every advertised axis now changes returned bytes and can be reconstructed by `observe_overrides`. Counts describe semantic structures rather than indirect aesthetic knobs.

**Baseline/rejected alternatives.** `palette_size=8` and `position_bias=scattered` were collapsed. `palette_kind`, `texture`, `gap_min`, and `n_distinct_colors` either did not control the output as advertised or obscured the actual semantic boundary. Keeping them as diagnostic metadata would still burden callers with non-exact controls, so they were removed.

**Probe/failure mode.** Focused tests cover exact round-trips and invalid values. The after override gate accepted 25,110/25,110 draws over 279 cases and 3 bands. Incompatible totals greater than `grid_w` fail explicitly rather than silently truncating.

## D3 — Use a four-profile deterministic curriculum

**Choice.** `sample_index mod 4` selects `canonical`, `mismatch`, `blocked`, `singleton`.

**Rationale.** The canonical ledger has only positive matching-pair examples. Three wrong rules fit every canonical pair: ignore endpoint color, ignore a third marker, and extend singletons. One profile per boundary makes any four consecutive demonstrations eliminate all three rivals.

**Alternatives rejected.** Randomly sprinkling negatives could leave complete lessons ambiguous. Making negatives opt-in textures would repeat the baseline failure because normal training would not see them. Combining all distractors in every grid would be efficient but visually dense and would make attribution harder.

**Probe/failure mode.** `lesson_identifiable` evaluates complete demo windows. The 100-lessons-per-band probe covers every cyclic start residue 25 times and reports 100/100 rival-refuting lessons in each band. It does not prove every arbitrary, non-scheduled subset is identifiable.

## D4 — Preserve explicit canonical anchors

**Choice.** The canonical profile uses 6x6, 7x7, or 8x8 square grids, 2..3 matching target columns, canonical colors, and no distractors. `MIN_STRICT_FRAC` is 0.20.

**Rationale.** Teaching negatives should not erase support near the original examples. One of four scheduled profiles yields 25% strict support in the larger probe, above the declared floor.

**Alternatives rejected.** Using only larger hard-band grids would weaken canonical support. Copying the canonical layouts exactly would reduce diversity and risk memorization.

**Probe/failure mode.** Profile-floor found at least one canonical hit in each band's 20-draw sample. Semantic-gate measured 142/600 strict hits (23.7%); the longer probe measured 125/500 (25%) per band.

## D5 — Bound dimensions to 6..12 and targets to 1..3

**Choice.** Grids are 6..12 in each dimension; target count is 1..3; each distractor count is 0..1.

**Rationale.** These ranges retain canonical scale, allow edge/interior variation, fit the four structures without crowding, and keep each column visually interpretable.

**Alternatives rejected.** The baseline hard range reached 14 and up to seven targets, which increased surface variation without adding semantic information. Dense multi-distractor scenes were deferred until the basic contract is admitted.

**Probe/failure mode.** The known domain limit is recorded in the probe. The generator rejects impossible column totals. This review makes no claim about dense scenes, multiple blockers, adjacent endpoints, or interacting columns.

## D6 — Keep colors broad outside canonical anchors

**Choice.** Canonical-only grids draw from `(2,3,4,5,7)`; teaching profiles can use all ARC foreground colors 1..9.

**Rationale.** The rule is color-generic, while canonical anchors should remain close to the source palette. Mismatch/blocker cases need distinct colors to make the exception observable.

**Alternatives rejected.** A fixed color per profile risks a color shortcut. Completely canonical-only colors reduce combinations and make distractor roles more repetitive.

**Probe/failure mode.** Diversity and the lesson probe report broad palette support. Structural validation checks ARC colors and semantics, not specific identities.

## D7 — Alternate an explicit edge anchor

**Choice.** `edge_anchor` deterministically alternates and, when true, places one target at rows `0` and `h-1`.

**Rationale.** This rules out a hidden “interior-only” positional assumption and gives an exact geometric control.

**Alternatives rejected.** A vague `position_bias=scattered` axis was unobservable. Random edge contact alone would not guarantee support in small samples.

**Probe/failure mode.** `observe_overrides` recovers the axis exactly. The long probe observes both values in every band.

## D8 — Represent rivals and witnesses as executable functions

**Choice.** Declare `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` using callable transformations/predicates.

**Rationale.** Names in prose do not establish that a rival fits the canonical examples or that a generated case actually refutes it.

**Alternatives rejected.** Hard-coded rival-name lists in the probe were rejected; the tool iterates the generator declarations so future edits cannot silently desynchronize the audit.

**Probe/failure mode.** The probe verifies that all three declared shortcuts fit all 3 canonical pairs, then measures exact disagreement and full-lesson refutation. New rivals must be added to the declarations and tests.

## D9 — Use an independent Python mirror for fast local tests, not as authority

**Choice.** `rule_mirror` supplies outputs for focused tests and the 1,500-pair lesson probe. Racket remains authoritative.

**Rationale.** Calling Racket for every high-volume lesson-probe pair would add substantial startup cost. A mirror makes exact semantic tests practical.

**Alternatives rejected.** Treating the mirror as final proof was rejected. The report labels its oracle and pairs it with independent Racket rule-smoke, semantic-gate, authority-sync, 12 materialized lessons, and a supported exact counterexample.

**Failure mode.** Mirror drift is possible; `RULE_HASH`, canonical pair checks, and independent gates are the guardrails.

## D10 — Add a reusable source-bound lesson probe

**Choice.** `workspace/lesson_probe.py` samples 100 disjoint five-pair lessons per band using hash-derived seeds and records source hashes, all start residues, uniqueness, observed axes, witnesses, disagreements, and lesson refutation.

**Rationale.** The battery's small lesson sample is a smoke test. The task has plausible rivals that fit every canonical pair, so larger lesson-level evidence was required.

**Alternatives rejected.** Overlapping sliding windows would inflate denominators; this probe uses disjoint windows. A single fixed start would miss schedule phase effects; all four start residues are balanced.

**Failure mode/limitation.** This is deterministic sampled evidence, not universal induction. It intentionally reports the sampler and domain limits.

## D11 — Preserve failing iterations and solve honesty

**Choice.** Keep red test logs, the externally interrupted before console, one blind solve, and one exposed post-repair solve with truthful exposure fields.

**Rationale.** They distinguish actual test-first development and visible-example solving from retrospective claims.

**Alternatives rejected.** Fabricating a failed solve or calling the post-repair solve blind would misstate the evidence.
