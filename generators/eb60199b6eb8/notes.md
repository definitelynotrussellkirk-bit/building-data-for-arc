# Working notes: eb60199b6eb8

## Current rule and authority

The unchanged canonical Racket rule treats rows independently on a fresh zero grid. A row produces an inclusive horizontal segment only when it has exactly two nonzero cells and both have the same color; every other row produces zeros. `RULE_HASH = 7d5c5a67ac1a` binds generator version 3.0.0 to that authority.

## Review-529f49df89b85e1d decision record

The prior sampler advertised dead or aliased palette/position/density/texture controls, had no rule pin or validator, missed every canonical profile in the profile-floor check, accepted unsupported overrides, and had no executable lesson contract. The prior rationale is otherwise unknown; imported associated notes contained no decision record.

Version 3.0.0 replaces that contract rather than preserving misleading aliases:

- observable axes only: `grid_h` 4..10, `grid_w` 5..12, `n_rows` 1..3, and `n_distinct_colors` 3..5;
- canonical 4×5/6/7 anchors every third schedule profile, plus broad and dense profiles;
- exact override round-tripping in every difficulty band;
- explicit rejection of unknown, retired, malformed, out-of-range, and incompatible controls;
- one mismatched pair and one A–B–A triple in every ordinary grid;
- executable rivals `connect_any_two`, `connect_outermost_same`, and `preserve_invalid_rows`;
- `EXAMPLES_NEEDED = 2`, because either generated demonstration contains both decisive witnesses; and
- no degenerate texture branches.

The only joint incompatibility is `grid_h=4` with `n_rows=3`: three valid rows plus the two mandatory decoy rows cannot fit.

## Evidence

- Before: `checks/before/checks/eb60199b6eb8_before_battery_summary.json` — 5 failed stages.
- Final generator SHA-256: `c309fdcb86cf2588b01e62784b5ff9a82ad1b658806a87ad48e07f5e1ee9efb2`.
- After: `checks/after/checks/eb60199b6eb8_after_battery_summary.json` — all 12 stages green.
- Portable focused tests: 42/42 at `checks/task-tests-final2/checks/task_tests.xml`.
- Rotation-required smoke: 12/12 lessons and 36/36 rotations.
- Larger census: 300/300 production lessons and 900/900 query rotations, 900 unique inputs, no declared-rival ambiguity.
- Minimal in-domain counterexample: `counterexamples/canonical_shortcut_witness.json`.

## Known limits and open findings

The validator describes the intended training domain, not every grid on which the Racket law is meaningful. Ordinary generated grids always contain exactly the two required invalid-row witness types, which is a presentation regularity; dimensions, valid-row count, palette size, colors, row placement, and endpoint positions vary. The semantic evidence is finite and covers declared rivals only. No Racket change or unresolved blocker remains for this repair.
## Current reviewer considerations

Source SHA-256: `c309fdcb86cf2588b01e62784b5ff9a82ad1b658806a87ad48e07f5e1ee9efb2`.

# Decisions for `eb60199b6eb8`

## D1 — Preserve the reference rule; bind to it explicitly

**Prior choice:** the Python generator had no `RULE_HASH`. The Racket authority itself passed before-repair rule smoke and authority sync.

**New choice:** keep the Racket/canonical rule unchanged and declare `RULE_HASH = "7d5c5a67ac1a"`.

**Reason:** the defect was in sampling, metadata, validation, and teaching support, not the row transformation. Changing a passing authority would add risk without repairing the observed failures.

**Evidence:** before and after authority-set SHA-256 are both `2bd868e1293d1ed3ce57060a7f9e97ab30a9725f1a4e74f8f629d1c170cc4da7`; see the two battery summaries.

## D2 — Retire dead controls instead of pretending to honor them

**Prior choice:** `palette_kind`, `palette_size`, `position_bias`, `density`, and `texture` were advertised even though some were ignored, aliases, single-valued, or degenerate branches that bypassed ordinary controls.

**New choice:** advertise only `grid_h`, `grid_w`, `n_rows`, and `n_distinct_colors`; reject every unknown or retired override.

**Reason:** exact control metadata is training provenance. Silently accepting a typo or dead axis creates examples whose labels do not describe the pixels.

**Rejected alternative:** keep the old names as aliases. This preserves ambiguous provenance and was the root of the baseline override failures.

**Probe:** exact minimum/maximum combinations round-trip in every difficulty band; invalid and retired controls are parametrically rejected in the focused tests.

## D3 — Use observable axis domains

- `grid_h`: 4..10
- `grid_w`: 5..12
- `n_rows`: 1..3 valid same-color pair rows
- `n_distinct_colors`: 3..5 nonzero colors visible in the input

`observe_overrides` derives all four values from returned pixels. The only declared joint incompatibility is `grid_h=4` with `n_rows=3`, because two mandatory decoy rows also need space.

**Rejected alternative:** make `n_rows` mean all occupied rows. That would hide the distinction between rule-bearing pair rows and teaching decoys.

## D4 — Anchor canonical profiles without collapsing diversity

Every third schedule profile is canonical-sized: 4 rows, width 5/6/7, two valid pair rows, and three foreground colors (four total colors including zero). The other profiles cover broader/dense layouts with 1 or 3 valid rows and 4 or 5 foreground colors.

**Reason:** the baseline produced zero canonical-profile hits in all 60 profile-floor draws. A deterministic finite schedule guarantees support while the independent layout RNG still changes colors, row positions, and endpoints.

**Rejected alternatives:**

- purely random canonical hits, which can miss a small gate sample;
- canonical-only generation, which would overfit the three source layouts;
- difficulty-specific override ranges, which made the same exact request succeed or fail depending on band.

## D5 — Put both decisive shortcut witnesses in every ordinary grid

Each generated input contains:

1. one separated two-color pair, refuting `connect_any_two`; and
2. one three-cell A–B–A row, refuting `connect_outermost_same`.

Both also refute `preserve_invalid_rows`. The valid pair rows remain separated same-color endpoints.

**Reason:** both weaker rules fit all three canonical training pairs. Merely producing correct labels is not enough; demonstrations must teach why invalid rows disappear.

**Retained witness:** `repo/generators/eb60199b6eb8/counterexamples/canonical_shortcut_witness.json` is a 4×5 in-domain example that refutes all three declared rivals.

**Limitation:** this fixed witness policy introduces a presentation regularity (two designated invalid-row types per grid). The lesson tests establish separation from declared rivals only, not all possible rules.

## D6 — Two demonstrations are sufficient for this schedule

`EXAMPLES_NEEDED = 2`. Because each individual ordinary grid carries both decisive decoys, every two-demo lesson tested separates all declared competitors.

**Evidence:** rotation-required semantic smoke: 12/12 lessons and 36/36 hold-outs. Large census: 300/300 production lessons and 900/900 rotations across easy/medium/hard, with 900 unique inputs and zero hook/materialization/scoring errors.

**Rejected alternative:** inflate the lesson to three or four examples to compensate for weak examples. Stronger individual demonstrations give more data value per token.

## D7 — Validator scope

`self_check` accepts all canonical inputs and the declared sampler domain, rejects malformed/ragged/non-integer grids, enforces 4..10 × 5..12 bounds, requires 1..3 valid separated same-color pair rows, and allows up to five foreground colors. `strict_canonical_like` uses the same lawful-domain check, yielding a measured strict fraction of 1.0 over 600 final semantic-gate draws.

**Reason:** the previous absence of a validator made profile and semantic claims unverifiable.

**Known limit:** the canonical Racket law is meaningful outside these training bounds. This validator describes the intended generated-data domain; it is not a mathematical characterization of every grid on which the rule can execute.

## D8 — No degenerate texture branches

No degenerate textures are advertised. Empty/all-invalid boards are lawful for the general rule but provide little teaching value and were not needed for the repaired training distribution.

**Rejected alternative:** retain special branches such as “no pairs” while ignoring the other overrides. That caused provenance mismatch in the baseline.

## D9 — Solve and audit separation

The blind task was completed before opening generator material. The post-repair solve was prepared from final generator hash `c309fdcb...` and honestly marked as exposed because the rule had been seen during review. The two audit targets were left source-identical; their authority-backed counterexamples are evidence only, not bundled repairs.

## 2026-10-24 review-e702987a9fcd90e6 — native parametric admission handoff

### Built family

The task-local native adapter exposes one episode-fixed parameter, `closure`:

- `horizontal_only` is the exact selected canonical program, SHA-256 `7d5c5a67ac1a9f8170fdb3247fadbef891cc3402414982933e55e442b90ac8b7`.
- `horizontal_then_vertical` first performs the canonical horizontal completion on a fresh zero grid (A), freezes that input-dependent intermediate, then completes only columns containing exactly two same-colored nonzero cells in that intermediate (B). B cannot select its columns or endpoints from the original sparse input.

The adapter supports 2–6 demonstrations and exactly four distinct novel queries per episode. The final query is a lawful 30×30 stress case. Inputs are paired across settings, private settings/programs/answers stay out of the public projection, and the first sequentially revealed query matches single-query projection.

### Verification retained

- Focused prototype suite: 26 passed after recorded RED failures.
- Native qualification: 4 jobs across both settings and two fresh seeds, 40 protected-Racket evaluations, unique finite survivors.
- Count-boundary replay: both settings at 2 and 6 demonstrations, 48 protected-Racket evaluations.
- Sequential witness: protected-Racket skip-A counterfactual changes the selected columns and final answer.
- Bounded learnability audit: 64 protected-Racket evaluations against five executable rivals; no tested rival fit every visible demonstration and disagreed on a query.
- Full task suite: 68 passed.

Evidence is bound by `workspace/parametric/evidence/manifest.json`; native qualification is under `checks/eb60199b6eb8/qualification/`. This is reviewer-reported `ready`, not owner acceptance, variant approval, training admission, or production API activation. The owner must replay qualification and acceptance on the exact integrated bytes.
