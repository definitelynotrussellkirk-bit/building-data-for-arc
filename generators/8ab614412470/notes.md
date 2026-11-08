# Current notes: 8ab614412470

## Intended rule and authority

Count every non-background color over the whole input grid. Replace colors that occur exactly once with background 0; preserve every cell of colors that occur at least twice. The selected canonical Racket rule was not changed. Generator v2.0.0 pins `RULE_HASH = "f20d2d2ae760"`; final generator SHA-256 is `c757bddacbc88dd55a88bf7111cefb4431258b8cdbf50e4f2f36e5cac1a1d6e4`.

## Baseline defect

The v1.2.0 generator always placed seven marks at fixed coordinates with multiplicities 3/2/1/1. It advertised dead or singleton axes, had no rule hash or semantic contract, rejected all four canonical inputs, emitted only palette-size 5 while canonical inputs use 6 or 7 colors including background, hit 0/60 canonical profiles, accepted unknown or inert overrides, and exposed degenerate textures as ordinary valid draws. The before battery was 5 green, 1 advisory, and 6 failed; see `checks/before/checks/8ab614412470_before_battery_summary.json`.

## Current curriculum

The exact constructive axes are:

- `grid_h`: 5..9
- `grid_w`: 5..9
- `n_repeated_colors`: 2..5
- `n_singleton_colors`: 2..4
- `repeat_pattern`: `pairs`, `mixed`, or `heavy`

Every consecutive four-sample block contains three canonical anchors (`5x7`, `5x8`, `6x6`) and one broad slot that cycles through the full declared domains. Repeated-color multiplicities are respectively all 2; one 2 plus remaining 3s; or one 2 plus remaining 4s. Every input has at least two singleton colors and a designated globally repeated pair in different rows and columns. Easy, medium, and hard preserve the same semantic profile while using pair Manhattan distance 2, an intermediate distance, and maximum corner-to-corner distance respectively.

All declared overrides are exact, observable through `observe_overrides`, deterministic, and fail closed on wrong types, out-of-range values, unknown keys, or unsupported difficulty values. There are no ordinary or degenerate texture aliases.

## Semantic contract

`strict_canonical_like` accepts every imported canonical input. `rule_mirror` implements the selected rule independently in Python. Three witnesses fire on every generated input and refute three named rivals:

- a surviving count-2 color refutes `keep_three_plus`;
- at least two singleton colors refute `erase_one_singleton`;
- a nonadjacent surviving pair refutes `adjacent_only`.

`lesson_identifiable` checks correctly labeled lessons against all three competitors. `EXAMPLES_NEEDED = 3`, and the four-slot schedule is exposed through `schedule_profile`/`SCHEDULE_PROFILES`.

## Verification and limits

The final 12-stage after battery is all green, 43 task-local tests pass, the shared semantic gate found 12/12 production lessons identifiable and 0/48 ambiguous rotations, and the larger census found 300/300 production lessons identifiable with 0/1,200 ambiguous rotations over 1,200 unique inputs. The task-local `workspace/distribution_probe.py` additionally checks deterministic replay, validator/observer behavior, schedule residues, witness/rival disagreement, and all cyclic four-example query rotations; its retained 400-sample report passed.

The contract is intentionally bounded to 5..9 grids, zero background, 2..5 repeated colors, 2..4 singleton colors, and multiplicities 2..4. The finite rivals are plausible shortcut checks, not a proof of unique induction against every possible rule. The schedule is deterministic by sample-index residue; positions and colors remain seed-random. No historical return was used as a design authority; decisions were based on the current pinned source, canonical record, shared contracts, before/after evidence, and the retained passing example named in the assignment.
## Current reviewer considerations

Source SHA-256: `c757bddacbc88dd55a88bf7111cefb4431258b8cdbf50e4f2f36e5cac1a1d6e4`.

# Decisions for 8ab614412470

## D1 — Preserve the selected rule; pin its authority

**Prior choice:** v1.2.0 implemented the intended transformation informally but omitted `RULE_HASH`.

**Decision:** leave the canonical Racket program unchanged and pin `RULE_HASH = "f20d2d2ae760"` in generator v2.0.0.

**Rationale and probes:** the baseline rule-smoke and authority stages were already green, and an independent Python oracle matches every canonical labeled pair. Changing authority would add risk without addressing the actual distribution defect.

**Failure mode/limit:** the pin guarantees identity to the selected rule version, not approval for training.

## D2 — Replace aspirational axes with five exact constructive axes

**Prior choice:** metadata advertised grid sizes, palette families, anchoring, asymmetry, fixed palette size, fixed position bias, and fixed color count, although most were inert, singleton, or inconsistent with generation.

**Decision:** advertise only `grid_h`, `grid_w`, `n_repeated_colors`, `n_singleton_colors`, and `repeat_pattern`. Reject unknown keys and invalid types/ranges. Add `observe_overrides` and no incompatible combinations.

**Alternatives rejected:** keeping diagnostic/inert axes would preserve misleading API surface; adding color-identity controls was unnecessary because semantic colors are interchangeable and are already randomized.

**Evidence:** all exact boundary cross-products pass in all four bands; final override stage is green. The before override stage had 10,995 findings.

## D3 — Use a four-slot canonical/broad schedule

**Decision:** sample-index residues 0, 1, and 2 anchor 5x7/palette-6, 5x8/palette-6, and 6x6/palette-7 profiles; residue 3 cycles through the complete declared domains.

**Rationale:** this guarantees a linked canonical-profile hit in every short band window while retaining broad support. A purely random sampler could miss profile-floor checks and make lesson composition seed-sensitive.

**Alternative rejected:** drawing every axis independently and hoping for canonical intersections. It offers superficially more randomness but weaker short-window coverage.

**Limit:** schedule branches are deterministic by sample index; random colors and placements still provide instance diversity.

## D4 — Vary multiplicities while preserving explicit shortcut witnesses

**Decision:** `pairs` uses all count-2 repeats; `mixed` uses one 2 and remaining 3s; `heavy` uses one 2 and remaining 4s. Every instance has 2..4 singleton colors.

**Rationale:** multiplicity variety prevents overfitting to one histogram, while a guaranteed count-2 survivor and multiple singleton colors refute two high-probability shortcuts in every example.

**Alternative rejected:** arbitrary multiplicities up to grid capacity. That enlarges the domain but weakens observability and can crowd small grids without improving the core lesson.

## D5 — Make the global-vs-local distinction present in every input

**Decision:** designate one repeated color as a two-cell pair in different rows and columns. Easy uses Manhattan distance 2, medium an intermediate distance, and hard maximum corner-to-corner distance.

**Original rationale:** the first implementation made the pair nonadjacent but ignored difficulty. The intermediate battery correctly flagged byte-identical bands.

**Revision:** add a failing regression, then make separation difficulty-dependent without altering semantic counts or profiles.

**Evidence:** `checks/task-tests-dead-bands-red/`, `checks/task-tests-dead-bands-green/`, and the final defect-lint pass.

## D6 — Add a finite executable semantic contract

**Decision:** declare rivals `keep_three_plus`, `erase_one_singleton`, and `adjacent_only`; map them to witnesses `pair_survives`, `multiple_singletons`, and `nonadjacent_pair_survives`; add `lesson_identifiable`, `strict_canonical_like`, `rule_mirror`, `EXAMPLES_NEEDED = 3`, and schedule metadata.

**Rationale:** correct labels do not ensure that demonstrations identify the desired global rule. Named competitors make that claim executable and inspectable.

**Limit:** three rivals are not an exhaustive hypothesis space. Reports use “no ambiguity found against declared rivals,” not proof of unique induction.

## D7 — Remove ordinary and degenerate textures

**Prior choice:** helpful textures were dead aliases and negative fixtures appeared in the ordinary valid domain.

**Decision:** expose no texture axis and set both texture tuples empty.

**Rationale:** this task's useful variation is structural/histogram-based. Texture labels added no lawful independent behavior.

## D8 — Align validator boundaries with canonical and generated support

**Decision:** accept rectangular 5..9 grids with ARC integer colors, background 0, 2..5 repeated colors, 2..4 singleton colors, repeated multiplicities 2/3/4, and at least one pair. Reject malformed/ragged/bool-valued grids safely.

**Rationale:** all four canonical inputs satisfy these conditions, as do all generated combinations. The prior validator rejected every canonical input by requiring 6..9 dimensions and exactly four nonzero colors.

**Limit:** the validator intentionally does not require the generated nonadjacent-pair layout, so canonical lawful inputs remain accepted.

## D9 — Build a reusable source-bound probe

**Decision:** add `workspace/distribution_probe.py` and a task test for it. It samples each band, checks replay, validation, observed profiles, schedule residues, witness/rival claims, and all rotations of each cyclic four-slot start.

**Rationale:** the shared battery is broad, while this schedule is small enough for a cheap task-specific exhaustive residue check. The tool reads declared rivals rather than duplicating a hard-coded expected list.

**Evidence:** `checks/distribution-probe.json` (400 samples, 64 cyclic-start rotations, pass).

## D10 — Evidence and historical leads

No historical return was used as a design lead. I used the current pinned source, current canonical record, `ARC-DESIGN.md`, the semantic/override contracts, the before battery, and the retained passing example named in the assignment. Failed iterations were retained rather than overwritten: initial task-test RED, intermediate dead-band battery, dead-band RED/GREEN, and probe RED/GREEN.
