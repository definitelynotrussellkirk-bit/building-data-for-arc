# Binary-Mask Teaching Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make every default lesson identify the canonical binary-mask component rule against color-grouping and nonzero-foreground shortcuts.

**Architecture:** Keep geometry and exact axes unchanged. Add deterministic palette assignment modes after shape selection, place one isolated 9 background witness, loosen validation only where the authority permits, and register executable shortcut mirrors. Extend the independent probe and exact counterexample so future reviewers can reproduce the semantic gap without trusting production helpers.

**Tech Stack:** Python 3.12, pytest, bundled Racket authority, packet review runner.

**Spec:** `generators/2c4efc97c37d/workspace/2026-10-23-binary-mask-teaching-design.md`

## Global Constraints

- Do not change `RULE_HASH` or canonical data.
- Preserve all five advertised exact axes and their domains.
- Every default draw must refute all registered rivals.
- Colors must remain literal ARC integers 0..9.
- Production source changes require matching focused tests and Racket execution.

## Review Focus

- Repeated-color components must have unequal true depths so color grouping cannot accidentally match.
- Mixed-color components must remain one 4-connected binary component.
- The 9 witness must be isolated from all foreground under the nonzero shortcut.
- Canonical 0-background, unique-color examples must remain accepted.
- Override boundary combinations must still construct without retries or geometry drift.

---

### Task 1: Independent semantic witnesses

**Files:**
- Modify: `workspace/onion_probe.py`
- Modify: `tests/test_generator.py`
- Create: `counterexamples/binary-mask-shortcuts.json`

**Interfaces:**
- Produces: `color_partition_output(grid)`, `nonzero_output(grid)`, `binary_mask_counterexample()`.

- [x] Write tests asserting the exact witness yields canonical `[[1,2,3]]` and disagrees with all three shortcuts.
- [x] Run the focused test and confirm failure because the new probe interfaces do not exist.
- [x] Implement the independent rivals and witness with no production imports.
- [x] Run the focused test and confirm it passes.

### Task 2: Generator palette topology repair

**Files:**
- Modify: `generator.py`
- Modify: `tests/test_generator.py`

**Interfaces:**
- Produces: default grids alternating `reused` and `mixed` component-color topology, each with an isolated 9 witness.

- [x] Write tests requiring every default draw to contain 9, refute the color-partition and nonzero rivals, and cover both topology modes.
- [x] Run the focused tests and confirm failure under version 3.0.0.
- [x] Implement deterministic color assignment, isolated-9 placement, authority-faithful validation, observables, and version/invariant updates.
- [x] Run focused tests and the whole task-local suite.

### Task 3: Lesson contracts, Racket parity, and retained evidence

**Files:**
- Modify: `generator.py`
- Modify: `tests/test_generator.py`
- Modify: `notes.md`
- Modify: `SUMMARY.md`

**Interfaces:**
- Produces: registered `color_partition_depth` and `nonzero_foreground_depth` rivals and matching witnesses.

- [x] Write tests requiring all rivals to be registered and every demo/query rotation to identify them.
- [x] Run tests and confirm the contract fails before registration.
- [x] Register rivals/witnesses and update mutation fixtures.
- [x] Run task tests, Racket parity, adversarial boundary checks, and staged after-tests.
- [x] Record exact findings, limitations, and hashes in the task notes and packet reports.
