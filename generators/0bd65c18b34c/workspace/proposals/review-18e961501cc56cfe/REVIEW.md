# Review: `0bd65c18b34c`

Task/source: generator `0bd65c18b34c`, version `3.1.0`, source SHA-256 `f9e74f2b1216ef76ee0ae0bf5189c6c7a8068b234334fb0df9ff559a12a738aa`.
Status: **routine selected-generator repair complete**; the separate `tie_break` extension is **proposed only**, not production-approved or training-admitted.
Defect → repair: the published balanced profile contained equal-distance cases but did not reliably teach the canonical row-major tie choice; it now contains a same-row tie whose output differs under a plausible rightmost rival.
Teaching guarantee: an alternating two-slot schedule puts a distinguishing tie lesson in every three-demonstration window, while explicit `scene_profile` overrides still take precedence.
Authority: canonical Racket text, canonical ledger, public four-profile axis, and `RULE_HASH = 9cd282956b9a` are unchanged.
Verification: 24/24 authored tests pass; semantic gate passes 600/600 strict draws, 378 witness hits, all three bands, 24 fixed-seed schedule/query rotations, and zero warnings/errors.
Compatibility probe: all 12 explicit profile/band combinations pass, all four profiles occur across 720 default draws, labels match independent/canonical authority, mutations are rejected, and global RNG state is isolated.
Prototype: two episode-level settings (`first`, `last`), three demonstrations and four distinct Racket-labelled queries per retained episode, exact visible-byte public IDs, and no hidden query answers in public files.
Known blocker: the issued frozen legacy test fails before collection in the relocated `task_tests` runtime because it hard-codes a canonical-data path; it was not modified. Portable authored tests pass.
Supplementary tickets: one lawful shortcut-refuting witness completed for `dfc4967f816f`; one pinned audit replay for `defba1ab4f90` reproduced the existing 11/11 scalar-contract defect without clearing or broadening that audit.

## Production repair

The canonical program selects the first square in row-major order when several red 2×2 squares are equally near a blue dot. The old canonical examples are also consistent with a plausible `topmost_then_rightmost` alternative, and the old `large_four_balanced` geometry did not turn its claimed tie lesson into a behavioral distinction.

The repair keeps the existing `large_four_balanced` public profile rather than adding a fifth profile. Its third and fourth squares are now on one row and seven columns apart. One forced blue dot lies in the aligned equal-distance position, so the canonical first-square choice and the rightmost rival move it to different cells. A second unaligned tie remains stationary, preserving the profile's published movement counts.

The generator now declares the rival, witness, semantic lesson hook, and a two-slot schedule. `schedule_profile(seed, sample_index, difficulty)` alternates `ordinary` and `tie_break`; malformed scalar arguments are rejected strictly. Tie slots force `large_four_balanced`, while a caller-supplied `scene_profile` remains authoritative.

The first attempted three-slot schedule was rejected during TDD: holding out its sole tie witness made two query rotations ambiguous. The final alternating schedule leaves a distinguishing witness in every three-of-four support set.

## Parametric prototype

`workspace/parametric/` contains a bounded task-local prototype with one hidden episode parameter:

- `tie_break="first"` is byte-for-byte the unique canonical Racket program shared by both canonical ledger rows.
- `tie_break="last"` changes exactly the equal-distance reduction comparator from `<` to `<=`.
- The setting is selected once per episode and is never exposed in the public challenge.
- Each retained setting has three demonstrations and four distinct lawful queries; every query contains a distinguishing same-row tie.
- Python and literal Racket execution agree, the demonstrations identify the setting, and public filenames equal SHA-256 of the exact visible bytes.

Retained public examples:

- `0942fd169808f682043773a09614a3fb3f578a9fed17b7073326402706d7da47.json`
- `c3e07ae64880cccdeaab7878b6fd88faa125029ac32b458f188c0892455e1bab.json`

The evidence status is `proposed`; it does not alter canonical approval, production defaults, or training admission.

## Verification evidence

- Authored regressions: `checks/main-repair/authored-tests-final-v4.log`
- Semantic gate and complete fixed-seed schedule census: `checks/main-repair/semantic-gate-after-v4/`
- Lint: `checks/main-repair/lint-after/`
- Compatibility/authority probe: `checks/main-repair/adversarial-probe-final-v2.json`
- Parametric evidence: `checks/parametric/0bd65c18b34c-tie-break/evidence.json`
- Frozen-test portability blocker: `checks/main-repair/task-tests-after-v3-command.log`
- TDD RED/GREEN receipts: `checks/main-repair/*-red.log` and corresponding `*-green*.log`

## Remaining limitation

The frozen issued test `tests/test_generator_0bd65c18b34c.py` derives canonical data with a fixed `__file__.parents[...]` path. In the portable staged runtime that points below the task and collection stops before any selected-generator assertion runs. The packet explicitly freezes that fixture, so the repair leaves it unchanged and records the blocker rather than masking it. A maintainer can port that test to `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` without changing generator behavior.
