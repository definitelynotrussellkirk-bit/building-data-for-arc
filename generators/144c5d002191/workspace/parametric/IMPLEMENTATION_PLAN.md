# Stamp orientation prototype implementation plan

**Goal:** Build a bounded episode prototype whose original orientation is the
exact canonical rule and whose alternative mirrors the cropped template left
to right before recoloring and stamping it.

**Architecture:** The prototype reads canonical authoring data through
`reviewer_support`, materializes one rule per episode, and obtains all labels
from `RacketBridge`. A small independent sampler provides asymmetric templates
with fully fitting and separated stamps. Private evidence contains rule and
source identities; public challenges contain demonstrations and query inputs.

**Spec:** `WORK/PARAMETRIC-RULES.md` and `WORK/RETURN-GUIDE.md`.

**Scope:** Only this directory, the assigned task's `tests/test_parametric.py`,
and `WORK/checks/parametric/`. No production generator or canonical edits.

## Work

- [x] Write portable tests for canonical byte fidelity, a lawful differing
  witness, deterministic input sampling, episode consistency, rival and query
  rotation identification, symmetric ambiguity, invalid values, and public
  redaction. Capture the initial missing-implementation failure.
- [x] Implement `stamp_orientation.py` with `materialize_program`,
  `generate_input`, `execute_program`, `generate_episode`, `assess_episode`,
  `public_challenge`, and a command-line evidence writer.
- [x] Run focused tests through the included wrapper, retain every genuine
  failed test log, and repair only failures within this prototype's scope.
- [x] Produce complete original and alternative episodes, canonical label
  comparisons, a differing witness, and an honest ambiguous teaching case.
- [x] Document exact commands, source identities, bounded support, and the
  distinction between this prototype and approved canonical production.

## Review focus

Tests must catch an unchanged alternative rule, a per-pair parameter draw,
mirroring the whole scene instead of the template, a query answer or parameter
leak in public output, and claims of identifiability from symmetric examples.
The root reviewer handles the repository battery and fresh delta replay.
