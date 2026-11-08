# Working notes: a9c4475d7cda

## Review outcome

Imported version 2.2.0 had a functional core rule but a stale public contract: several advertised controls were ignored, the rule hash was not pinned, helpful-texture declarations were dead, `self_check` accepted destructive mutations, and canonical demonstrations admitted the `count == 2` shortcut.

Version 3.0.0 keeps the canonical rule unchanged and rebuilds the generator around three exact observable controls:

- `grid_h`: integer 9..17
- `grid_w`: integer 9..17
- `count_profile`: `canonical_bridge`, `balanced`, `sparse`, or `dense`

Every value is legal in every difficulty band. Default weighting changes by band, but override legality does not. All profiles contain panel counts 1, 2, and 3; panel assignment and cell positions are shuffled.

## Semantic contract

The strongest canonical-fitting shortcut is `count == 2` (5/5 canonical pairs). `count_three` is its witness. The nearby `nonempty` rival is paired with `count_one`. These are executable under `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.

The retained exact Racket counterexample is `checks/shortcut-a9c4475d7cda/counterexample.json` in the review return. The 300-lesson census found zero ambiguous lessons and refuted every declared rival in every easy, medium, and hard lesson.

## Validation and tests

`_parse_grid` is the shared structural authority. It checks rectangular integer grids, colors 0/6/8, dimensions, exactly two complete divider rows/columns, no stray 8s, minimum band sizes, and panel counts. `self_check` accepts declared generated profiles and the canonical 1/2-only signature.

Task tests live in `tests/test_generator.py`. They cover all five canonical pairs, exact overrides in all bands, invalid override rejection, deterministic distribution, semantic counterexamples, and malformed/mutated grids. The portable stage reports 44/44 passing tests on the reviewed source hash.

## Authority record

The selected base-solution `target_code` was synchronized exactly to canonical `program_solution`; the prior minified representation remains in `raw_code`. This was a text/provenance repair, not a Racket semantic change.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51`.

# Decisions — a9c4475d7cda

## D1 / R1 — Replace, rather than emulate, the stale public axis surface

**Choice.** Publicly expose only `grid_h`, `grid_w`, and `count_profile`, and reject unknown or ill-typed overrides.

**Rationale.** The imported generator advertised controls such as `six_min`, `six_max`, `density_kind`, `anchor_corner`, `asymmetry_force`, `palette_size`, and `include_decoy`, but production sampling did not make them exact observable contracts. Keeping names that have no pixel-level meaning would preserve the root defect. The three retained controls can be reconstructed from every generated grid by `observe_overrides`.

**Alternatives rejected.** I rejected (a) silently accepting old names, because that recreates override drift; (b) implementing all old knobs, because several overlap or describe weak teaching texture rather than task semantics; and (c) declaring many incompatible combinations, because the core task does not require them.

**Probe.** `test_exact_axes_are_honored_and_observable_in_every_band` checks all four profiles in default/easy/medium/hard, while the official override stage exhausts the advertised domains. Evidence: `checks/after/checks/a9c4475d7cda_after_override_results.json`.

**Limit.** Difficulty changes default sampling weights, not legality. It does not promise monotonically harder instances.

## D2 / R1 — Use 9..17 dimensions in every band

**Choice.** Make each dimension independently exact over 9 through 17 in every difficulty band; weight defaults toward smaller/easier and larger/harder shapes without clipping overrides.

**Rationale.** Three panel bands plus two divider lines require at least 8 cells, but a minimum of 9 gives multiple legal band partitions while preserving canonical-like 11×11 support. A common domain across bands avoids the previous “declared globally, rejected by band” failure mode.

**Alternatives rejected.** Band-specific legal ranges were rejected because they turn an exact axis into a conditional contract. A fixed 11×11 generator was rejected because it would unnecessarily remove lawful diversity.

**Probe.** The task regression forces 9×17 under every band. The distribution test samples 96 instances per band and requires at least 12 distinct shapes plus recurring 11×11 support.

## D3 / R2 — Encode threshold evidence with four exact histograms

**Choice.** Use four count profiles:

- `canonical_bridge`: `{1:5, 2:3, 3:1}`
- `balanced`: `{0:2, 1:2, 2:3, 3:2}`
- `sparse`: `{0:4, 1:3, 2:1, 3:1}`
- `dense`: `{0:1, 1:1, 2:3, 3:4}`

Each profile is shuffled across the nine panels.

**Rationale.** Every lesson needs both sides of the threshold and a value above two. Counts 1, 2, and 3 are the smallest witnesses that distinguish `>=2` from both `>0` and `==2`. Multiple histograms prevent a solver from keying on one global number of positives or one density regime.

**Alternatives rejected.** Purely random 0..4 counts were rejected because a lesson can accidentally omit the crucial count-3 witness. A single fixed histogram was rejected as an avoidable global shortcut. Counts above three were not required because they add visual clutter without strengthening the threshold distinction.

**Probe.** The exact-two counterexample is retained in `checks/shortcut-a9c4475d7cda/counterexample.json`; the 300-lesson census verifies per-lesson rival refutation in every band.

**Limit.** The histogram names themselves are generator metadata, not information shown to a solver.

## D4 / R2 — Make rivals and witnesses executable

**Choice.** Declare `exactly_two` and `nonempty` as callable semantic rivals, with `count_three` and `count_one` witnesses; mark `exactly_two` as the canonical shortcut and both as lesson competitors.

**Rationale.** Textual claims about lesson quality are not replayable. Executable declarations let the semantic gate and census score the actual assembled lessons against source-bound alternatives.

**Alternatives rejected.** A single `lesson_identifiable=True` assertion was rejected because it would not explain or test which alternative was eliminated. A larger speculative rival catalog was deferred because it would dilute attention from the strongest canonical-fitting rule without evidence.

**Probe.** Canonical fit is 5/5 for `exactly_two`; all 300 final lessons refute it. The `nonempty` rival is already refuted by canonicals but remains a useful boundary check.

## D5 / R3 — Centralize structural parsing

**Choice.** Use `_parse_grid` as the single structural authority for validation, override observation, the Python rule mirror, and semantic probes.

**Rationale.** The baseline validator checked too little, allowing malformed grids to be treated as lawful. One parser removes disagreement among helpers and returns actionable diagnostics instead of throwing from `self_check`.

**Alternatives rejected.** Independent ad hoc checks in each hook were rejected because they can drift. Requiring generated profiles only was rejected because canonical examples have a legitimate 1/2-only signature and must remain accepted.

**Probe.** Tests mutate a divider, add a stray 8, insert an unknown color, erase all sixes, and supply malformed/noninteger grids. The pre-fix RED run is `checks/tdd-red.log`; the final portable run is `checks/task-tests/result.json`.

## D6 / R4 — Synchronize selected authority text without changing behavior

**Choice.** Set selected `target_code` exactly to the canonical formatted `program_solution`, preserve the previous minified form in `raw_code`, and label the record `synced_to_canonical_program_solution`.

**Rationale.** The baseline authority check already established execution parity. Exact text synchronization removes avoidable provenance ambiguity while retaining the archival representation.

**Alternatives rejected.** Rewriting the Racket rule was rejected because no semantic defect was found. Deleting the archival code was rejected because it would discard provenance.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` all pass in the 12-stage battery.

## D7 — Test from behavior outward

**Choice.** Preserve the failing TDD run, add 44 task-local tests, run the full battery, run the portable task-test stage, then run a 100-lessons-per-band source-bound census.

**Rationale.** The tests lock the root defects; the shared stages test repository contracts; the census tests complete lesson assembly rather than merely witness frequency.

**Alternatives rejected.** A small random smoke sample alone was rejected because it cannot establish per-lesson rival refutation. Treating the generated Python mirror as the final oracle was rejected; the retained shortcut output was obtained through the supported Racket `apply` command.

**Limit.** This remains finite testing. The census explicitly states that it is not a universal identifiability proof.

## D8 / A1–A2 — Do not patch audit targets

**Choice.** Leave `c53c24435976` and `71982ba2b59e` unchanged and retain source-bound counterexamples plus official failing stages.

**Rationale.** The assignment requested adversarial review, not cross-task repair. Editing them would expand the allowed delta and obscure ownership.

**Probe.** A1 is reproduced by `code=1` yielding observed code 3 and a different Racket output. A2’s shape proxy fits all five canonicals, while an in-domain hard sample disproves it; the missing piece is an executable lesson contract guaranteeing such refutation.

## D9 — Preserve solve separation and exposure declarations

**Choice.** Complete the unrelated blind solve before target inspection, then prepare a new post-repair solve from the final generator bytes and use only visible examples during that episode.

**Rationale.** This separates independent solving evidence from repair knowledge and binds the final teaching check to the exact repaired source.

**Limit.** The final solve is not blind: earlier exposure is correctly `yes`. It is evidence that the visible lesson teaches the threshold, not an independent discovery of the rule.

## Current task-local parametric prototype

The current `min_panel_count={1,2,3}` proposal combines `review-ae31e484134c872a`
and `review-fdc6a9b2aee6af87` while preserving the production generator, canonical
examples and exact default threshold-2 authority. The existing API name and four
lawful profile families are retained. Prototype profile order now starts balanced
so even one threshold-1 demonstration refutes constant masks; counts independently
support `1..16`. Every pair distinguishes the declared thresholds, with fixed
settings and Racket labels.

Exact saved programs, full canonical source guards, strict scalar/label types,
duplicate preflight, physical visible-ID emission order and a source/program/
label/certificate replay verifier are selected. The new parameter name
`threshold` and the duplicate alternative implementation are not selected. Prior
reviewer checks and official qualification remain prior-source provenance; they
do not qualify merged bytes. Current owner checks and disposition are bound in
[evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json).

All variants remain proposed and unaccepted, with training_admitted=false. This
change does not refresh production approval, resolve audits, claim universal
identifiability or establish learning benefit.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a9c4475d7cda/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
