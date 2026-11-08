# Working notes: 1198580cc354

## 2026-10-06 review repair

The imported `1.1.1` generator had eight advertised axes, including inert
single-value controls and texture aliases; accepted unknown controls; sampled
only a subset of declared ranges; included malformed negative textures in the
ordinary domain; and had a one-condition `self_check`. It also had no exact
rule binding or semantic lesson contract. The hard band had zero exact
canonical-profile support.

The strongest canonical-fitting shortcut found was **ignore color 1**: no
canonical input contains a color-1 seed, so a solver can reproduce every public
pair while treating 1 as background. A prior review also supplied a useful
lead: lessons whose demonstrations omit blockers permit an **ignore blockers**
rival. The current source resolves both rather than merely documenting them.

Version `2.0.0` now:

- pins `RULE_HASH = "018c975f3e7f"`;
- exposes only exact observable axes (`grid_h`, `grid_w`, `seed_count`);
- cycles canonical-profile anchors in every difficulty band;
- includes color 1, at least one blocker, and at least one unblocked seed in
  every ordinary input;
- validates the complete input grammar and rejects the former degenerate
  impostors;
- provides an independent Python rule mirror, three executable rivals, three
  witnesses, a canonical-shortcut declaration, and a lesson-identifiability
  hook;
- includes task-local regression tests under `tests/test_generator.py`.

The selected Racket authority was not changed. The semantic contract is finite:
it proves only that the named rivals are refuted on the sampled/generated
manifold, not that no imaginable alternate rule exists.
## Current reviewer considerations

Source SHA-256: `f0c577ab1bb3d669ec1d787e9678e084f5ce386ea47d8b8fc2a709eff20c6a69`.

# Decisions for 1198580cc354

## Scope and authority

**Decision D1 — keep the selected Racket rule unchanged.**

- **Original rationale:** not recorded in the imported task files. The canonical
  examples and selected rule agree on the same operation: each nonzero top-row
  seed projects downward until a color-9 blocker in its own column.
- **Alternatives considered:** edit the authority to match the narrow generator;
  reinterpret 9 as a global blocker; or make color 1 special.
- **Probe:** the baseline rule smoke and authority-sync stages were already green;
  the blind visible-only solve independently recovered the same rule; final
  differential checks stayed green after the generator rewrite.
- **Choice:** preserve the canonical authority and repair only the input
  distribution, validation, tests, and documentation.
- **Failure mode avoided:** changing a correct authority would silently relabel
  canonical and generated data instead of fixing the teaching defect.

## Public controls

**Decision D2 — expose only `grid_h`, `grid_w`, and `seed_count`.**

- **Original state:** nine advertised keys, including aliases, singleton enums,
  inert palette/texture choices, and ranges the sampler did not realize. The
  original rationale is unknown.
- **Alternatives considered:** retain every old key as a compatibility alias;
  mark dead axes diagnostic; or replace the contract with exact observable
  controls.
- **Probe:** baseline lint/defect/override checks found dead textures, unprobed
  singleton axes, range mismatch, missing observations, thousands of rejected
  advertised combinations, and acceptance of unknown keys.
- **Choice:** three integer axes with exact ranges: height `7..10`, width `7..12`,
  and seed count `2..4`. Every Cartesian combination is constructively valid in
  every difficulty band, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS = []`.
- **Verification:** final override matrix accepted and exactly observed
  `6300/6300` draws across 70 cases and three bands; unknown and mistyped values
  fail loudly.
- **Limitation:** blocker count, placement, seed columns, and colors remain keyed
  nuisance variation, not user controls.

## Default profile schedule

**Decision D3 — cycle four exact canonical profiles plus two broader profiles in
every difficulty band.**

- **Original state:** difficulty-specific random bounds; the hard band had
  `0/20` exact canonical-profile hits. The source did not explain why canonical
  scale disappeared in hard mode.
- **Alternatives considered:** sample only canonical dimensions; retain the old
  broad random bounds; or schedule a mixture.
- **Choice:** six named profiles: canonical `7×8/3 seeds`, `8×9/3`, `8×10/3`,
  `9×7/2`, plus broad `10×12/4` and `7×12/4`. Difficulty offsets change order,
  not support.
- **Probe:** the public `schedule_profile(seed, sample_index, difficulty)` hook is
  executable and enumerated by `SCHEDULE_PROFILES`.
- **Verification:** final profile floor measured `41/60` exact canonical-profile
  hits and at least one in every band; semantic census visited all six profiles.
- **Limitation:** the default shape set is intentionally discrete. Exact overrides
  still cover every supported intermediate size.

## Teaching signal

**Decision D4 — every ordinary input contains color 1, at least one blocked
beam, and at least one unblocked beam.**

- **Original state:** blocker placement was independent with probability 0.55,
  so an entire three-example lesson could omit blockers. No canonical input
  contains color 1.
- **Prior lead used:** source-matched audit
  `review-7e59c84bf90dd5ed:v0001` showed seed 916, indices 0–3, where three
  blocker-free demonstrations allowed an `ignore blockers` rival that failed
  only on the query. It was treated as a hypothesis lead and rechecked against
  the pinned baseline, not as current measurement.
- **Alternatives considered:** merely increase blocker probability; schedule one
  decisive example per three-example window; or make every example decisive.
- **Choice:** every ordinary grid has `1..seed_count-1` blocked columns and thus
  both blocked and unblocked beams. Color 1 is forced into the distinct seed
  palette on every draw.
- **Why stronger:** arbitrary query rotations and lesson truncation are less
  fragile when each individual example refutes the named shortcuts.
- **Verification:** each of the three semantic witnesses fired on `600/600`
  final semantic draws; 300 production lessons and all 1,200 held-out query
  rotations had zero named-rival ambiguity.
- **Limitation:** this proves only the declared finite rivals. It does not prove
  universal rule induction.

## Rival set

**Decision D5 — make three plausible alternatives executable.**

1. `ignore_blockers`: continue each beam through zero cells below a 9.
2. `global_first_blocker_row`: stop every beam at the earliest blocker row.
3. `ignore_color_1`: treat 1 as background while handling colors 2–8 normally.

- **Rationale:** the first came from prior source-matched evidence; the second
  tests column locality; the third is the strongest shortcut that fits every
  canonical pair because canonical inputs contain no color-1 seed.
- **Alternative considered:** document shortcuts only in prose.
- **Choice:** export `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`,
  `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`, and make
  `lesson_identifiable` execute them.
- **Probe:** the retained color-1 witness at seed 119/index 3 differs from Racket
  authority in six cells; see `checks/question/`.
- **Failure mode:** new plausible rivals can still be discovered. The workspace
  guide tells future agents to add them as executable contracts.

## Validation grammar

**Decision D6 — accept the complete observed task grammar, not only generated
byte patterns.**

- **Original state:** `self_check` required only one nonzero/non-9 cell in row 0;
  it accepted blank-like, full-color, solid 2×2, top-row blocker, and malformed
  degenerate scenes.
- **Alternatives considered:** validate generated provenance only; require both
  blocked and unblocked columns in all accepted inputs; or recognize the broader
  canonical grammar.
- **Choice:** require dimensions `7..10 × 7..12`, 2–4 distinct seed colors in row
  0, only 0/9 below row 0, blockers only in seed columns and rows `2..h-2`, at
  most one blocker per seed column, and at least one blocker.
- **Canonical exception deliberately preserved:** accepted inputs may have all
  seed columns blocked, because canonical train pair 0 does. The stronger
  blocked/unblocked condition is a sampler guarantee, not a validator rule.
- **Verification:** all four canonical inputs pass; 60 default self-check draws
  pass; task-linked mutation fixtures and focused malformed cases are rejected.
- **Limitation:** inputs with no blockers remain outside this generator's
  accepted teaching domain even though the authority can execute them. That
  restriction is intentional because blockers are the core distinction being
  taught.

## Demonstration count and order

**Decision D7 — declare `EXAMPLES_NEEDED = 3` and support arbitrary query
rotation.**

- **Original rationale:** unknown; the assignment's production lesson shape is
  three demonstrations plus one query.
- **Alternative:** declare one example sufficient because each generated grid is
  individually decisive against the current rival set.
- **Choice:** retain three to match production assembly and provide redundancy.
- **Verification:** focused tests check every query rotation for 12 cyclic starts
  in all four difficulty settings; the semantic battery required rotations and
  found `0/48` ambiguous; the larger census found `0/1200` ambiguous rotations.
- **Limitation:** the census does not enumerate every seed or every undeclared
  hypothesis.

## Tests and reusable tooling

**Decision D8 — keep review logic task-local and portable.**

- Added `tests/test_generator.py` with 61 tests covering canonical parity, exact
  boundaries, invalid controls, profile support, deterministic generation,
  mutation rejection, semantic rivals, public schedule API, and lesson rotations.
- Tests use `reviewer_support.find_root` and `canonical_pairs`, so the copied
  task-test runtime does not depend on repository depth.
- Added a documented inspection API in `workspace/README.md` rather than an
  external ad hoc script that future agents would have to rediscover.
- **Failure encountered:** the first schedule hook used the wrong public
  signature. The semantic gate caught `600/600` exceptions; a regression test
  was added before correcting it. The failed intermediate evidence remains in
  `checks/after/`.

## Self-review of the repair

The main new restriction is that every ordinary lesson always includes color 1
and mixed blocker status. That makes the named distinctions explicit but could
encourage a superficial expectation that color 1 is always present. The rule
itself and validator do not depend on color 1, exact overrides do not alter the
semantic behavior, and the canonical examples provide non-color-1 cases; this
is accepted as a teaching trade-off rather than a claim that the production
domain is exhaustive.

The finite rival suite also cannot certify unique human induction. Results are
reported as “no ambiguity found against declared rivals,” never as a proof that
no alternate rule exists.
