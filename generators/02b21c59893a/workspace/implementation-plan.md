# Offset-anchor curriculum repair implementation plan

**Goal:** Replace the ambiguous fallback-heavy sampler with an exact five-role curriculum that teaches every selected-rule branch and survives all four-demo query rotations.

**Architecture:** `generator.py` owns a constructive profile sampler, broad structural validator, exact profile observer, Python rule mirror, four rivals, witnesses, and lesson hook. `workspace/reference_probe.py` independently mirrors the rule and rivals for tests and future audits. `tests/test_generator.py` pins behavior and parity.

**Tech stack:** Python 3, existing `GenCtx`, pytest, canonical Racket bridge.

## Tasks

1. Write independent probe and failing regressions for the rule pin, canonical pairs, profile contract, schedule, rivals, prior seed-861 defect, and Racket parity.
2. Replace the production generator with the five-role constructive sampler and strict exact-axis contract.
3. Run focused tests RED then GREEN; diagnose root causes rather than weakening assertions.
4. Run task tests, semantic required-rotation gate, complete battery, and 300-lesson rotating census; retain failures and final reports.
5. Complete exposed solve, question answer, two assigned audits, maintainer brief, replay check, and return packaging.

## Rulings

- The extracted packet is not a Git repository, so worktree and commit steps are impossible. Preserve every source hash, command, log, and replay result in packet evidence instead.
- The canonical selected Racket source is unchanged. The generator domain requires a blue source because the selected rule calls `first` on blue points; no-blue fallback is neither canonical nor reference-lawful.
