# Current account: 8d2ecf358469

## Intended rule and admitted input grammar

The input contains exactly three separated nonzero monochrome 4-connected components, one component per color, on background 0. The output is a bar chart with one row per color in increasing numeric color order. Each row contains that color for exactly the component's cell area, left-aligned and padded with 0 to the largest component area.

The selected Racket authority floods nonzero cells without respecting color while finding objects, so differently colored components must not touch orthogonally. This generator deliberately teaches the six published-pair grammar rather than the broader, unsupported claim that multiple same-color components should be summed. Equal component areas remain lawful because rows are keyed by color, not area rank.

The current rule pin is `RULE_HASH = e8095729a5e6`; no Racket or canonical source changed in this review.

## Current generator decisions

- `VERSION = 2.1.0` because the deterministic lesson schedule changed.
- Ordinary inputs use canonical-scale grids, three distinct colors, and component areas in the authority-safe 2..5 range.
- The five scheduled profiles are `2-3-4`, `3-2-4`, `3-4-5`, `4-3-5`, and `2-5-4`.
- The older `2-4-5` profile remains a valid explicit override for compatibility, but is not part of the five-slot production schedule.
- Every generated draw includes an irregular component and a component-position ordering counterexample so bbox-area and spatial-order shortcuts are not silently taught.
- `sample_index` must be a nonnegative built-in integer at both public entry points. Booleans, floats, strings, and negatives raise `ValueError` rather than being coerced.

## Why the schedule changed

The prior five-demo schedule, inherited from return `local-random-679a1953ab38`, was sound for the production policy of five demonstrations followed by the sixth query: every demonstration window included the sole width-4 profile. A 300-lesson rotated census exposed a stronger downstream requirement. In 240 of 1,800 leave-one-out query rotations, holding out that sole width-4 pair left five width-5 demonstrations, so the declared `always_use_output_width_5` rival survived.

Adding `3-2-4` gives every six-pair window two width-4 witnesses. After any one pair is held out, at least one width-4 demonstration remains. The profile also reinforces that rows are not sorted by area. Replacing an existing override outright was rejected because it would break a public control; retaining `2-4-5` as an unscheduled override preserves compatibility.

## Evidence and checks

- Before battery: 11/12 green; `defect_lint` failed because invalid scalar `sample_index` values were accepted (`checks/before/`).
- Intermediate rotated census: 300 production lessons clean, but 240/1,800 rotated lessons ambiguous against fixed-width-5 (`checks/lesson-census.summary.json`; full report retained as `.json.gz`).
- Final battery at generator SHA-256 `0a2f07f4e9919201735ee47b53303c0c036c100544a8bdeeb254d40d53c0a4c2`: 12/12 green (`checks/final-after/`).
- Required-rotation semantic gate: pass (`checks/required-rotations-final/`).
- Final large census: 300/300 production lessons and 1,800/1,800 query rotations unambiguous against all declared rivals; 1,800 unique inputs (`checks/lesson-census-final.summary.json`; full report retained as `.json.gz`).
- New portable regressions: 7/7 pass, covering strict scalar validation and all 3 bands × 5 schedule starts × 6 query holdouts (`checks/focused-tests-final.log`).

## Known limits and open findings

These checks are finite and cover only the declared rivals plus the shared bounded generic search; they do not prove unique induction against every possible hypothesis. The ordinary grammar remains intentionally narrower than every grid the Racket program can execute. Any future change to `SCHEDULE_PROFILES`, `EXAMPLES_NEEDED`, component multiplicity, or contact rules requires rerunning both the sliding/rotation rival audit and selected-authority parity.

The packet's original `tests/test_generator_8d2ecf358469.py` is a frozen fixture and was restored byte-for-byte. Its fixed `Path(__file__).parents[1]` canonical path causes the portable task-test preflight to stop before pytest; it also pins the previous version string. Per packet instructions it was not rewritten. New tests use `reviewer_support`, but the isolated task-test stage remains blocked until the frozen fixture is migrated by the maintainer (`checks/task-tests-frozen-final/`).

## Maintainer portability correction

The inherited frozen fixture used a legacy script import, fixed-depth data lookup, and a VERSION2.0.0 assertion after the accepted repair became2.1.0. Migrated only source/data lookup to reviewer_support and advanced the explicit version pin; canonical rule/pair, authority-copy, override, lesson, witness, mutation and RNG assertions remain. The supported isolated task-test stage now passes all13 tests (six retained plus seven reviewer additions). Original reviewer preflight failure and the owner intermediate loader-unpacking failure are retained in var/review/return-b74b5b5c70306a18-validation; this does not relabel the original battery or claim a new semantic census. Generator/rule bytes are unchanged.
## Current reviewer considerations

Source SHA-256: `0a2f07f4e9919201735ee47b53303c0c036c100544a8bdeeb254d40d53c0a4c2`.

# Decisions

## D1 — Preserve the selected semantic rule and narrow component grammar

**Choice.** Keep the rule and `RULE_HASH e8095729a5e6` unchanged. Continue admitting exactly three separated monochrome components, one per color.

**Rationale.** All six canonical pairs, Racket smoke checks, and authority-sync checks already agree. Associated return `local-random-679a1953ab38` correctly identified that the selected Racket implementation uses color-blind nonzero connectivity while the examples identify only one component per color. Widening to touching colors or repeated same-color components would teach behavior not established by the examples.

**Rejected alternative.** Broaden `self_check` merely because Racket returns a value. Oracle executability is not the same as a justified training domain.

**Failure mode to monitor.** A future canonical/rule change involving repeated colors or orthogonal cross-color contact would invalidate this grammar decision.

## D2 — Enforce a strict scalar `sample_index` contract

**Choice.** Require a nonnegative built-in integer in both `schedule_profile` and `generate`.

**Rationale.** The before defect lint reproduced acceptance of booleans, floats, numeric strings, and negatives. Coercion creates aliases between nominally distinct public requests and lets negative indices silently select from the end of a schedule.

**Rejected alternative.** Continue `int()` coercion for convenience. It makes invalid inputs appear deterministic rather than failing loudly.

**Probe.** `tests/test_sample_index_contract.py`; red before the repair and green after it.

## D3 — Make the five-demo curriculum robust to arbitrary query rotation

**Choice.** Add scheduled profile `3-2-4`, retain two width-4 profiles in every cycle, and leave `2-4-5` available only as a compatible explicit override.

**Rationale.** The production-order schedule was clean, but the first 300-lesson census found 240 ambiguous rotations out of 1,800. Holding out the sole width-4 pair left five width-5 demonstrations, allowing `always_use_output_width_5` to survive. With two width-4 profiles, any single holdout leaves a refuting witness.

**Rejected alternatives.**

1. **Declare the curriculum ordered-only.** Rejected because the required review explicitly exercises query rotation and downstream reuse benefits from arbitrary holdout safety.
2. **Duplicate the same `2-3-4` profile under another public name.** Rejected because `observe_overrides` could not distinguish identical signatures honestly.
3. **Remove `2-4-5` from the public API.** Rejected because it was already an advertised exact override.
4. **Widen areas beyond 5.** Rejected as unnecessary distribution drift away from the canonical area range.

**Probes.** `checks/rotation-pre-fix-reproducer.json`, `tests/test_lesson_rotation_contract.py`, strict semantic gate, and `checks/lesson-census-final.summary.json`.

## D4 — Advance generator version, not rule hash

**Choice.** Change `VERSION 2.0.0 → 2.1.0`; keep `RULE_HASH` unchanged.

**Rationale.** Valid sample indices now select a different deterministic schedule, so generator provenance should distinguish old and new outputs. The semantic transformation and Racket source did not change.

## D5 — Keep the frozen fixture frozen

**Choice.** Restore `tests/test_generator_8d2ecf358469.py` byte-for-byte and put new tests in separate files.

**Rationale.** The assignment explicitly marks the baseline root fixture as nonpatchable. Rewriting its path logic made a temporary isolated run green but would have violated that contract, so that iteration was discarded. The genuine final stage reports the fixed-path preflight blocker.

**Rejected alternative.** Ship the rewritten frozen fixture or monkeypatch it. Either would hide a retained-harness problem rather than preserve evidence.

**Limitation.** The portable stage aborts before collecting the seven new tests. They were therefore run explicitly through the selected source layout and will need maintainer fixture migration for a fully green isolated task-test stage.

## D6 — Audit targets remain unchanged

The two drawn audit targets were inspected and reproduced, but their sources were not edited. `a77893c9c05c` rejects canonical dimension-3 frames; `f22baf82ea81` retains a centered-solid-inner shortcut. Details and source hashes are in `AUDIT.md` and `checks/audit/`.
