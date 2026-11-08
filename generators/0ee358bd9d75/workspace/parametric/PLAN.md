# Section frequency parameter implementation plan

**Goal:** A task-local, runnable prototype for `selection=most_frequent|least_frequent`.

**Architecture:** Keep the canonical Racket program byte-for-byte for the default.
The alternative changes only the frequency sort direction. A deterministic input
sampler draws four independent lawful grids without consulting the selection;
each section has two or three nonzero colors and unique extrema. The episode
builder selects the rule once and derives every label through `RacketBridge`.

**Tech stack:** Python standard library, existing reviewer helpers, existing
offline Racket bridge. No shared runtime or catalog edits.

**Spec:** `WORK/PARAMETRIC-RULES.md` and the parent agent's scoped assignment.

## Constraints and review focus

- Preserve zero-divider partitioning and row-major compact output positions.
- Default program must equal the catalog's canonical program exactly.
- Three demonstrations and one query; every one of four holdout rotations must
  distinguish the two declared settings using visible demonstrations.
- Output labels must come from Racket, with Python used only as an independent
  check. Record source/program/input hashes, seeds, results, commands and limits.
- Public files contain only demonstration pairs and query inputs.
- Reject unsupported selections, malformed grids, tied extrema and invalid
  scalar controls rather than silently choosing a rule or thinning an episode.

## Task 1: Executable rule and episode prototype

- [x] Write focused tests for canonical compatibility, exact differing witness,
  reproducibility, lawful unique extrema, once-per-episode selection, all demo
  rotations, malformed requests and public/private separation.
- [x] Run tests and retain the expected missing-prototype failure.
- [x] Materialize both exact Racket programs and implement `prototype.py`.
- [x] Run focused tests through the offline Racket wrapper and retain results.

## Task 2: Bounded authoring evidence

- [x] Test an evidence census on two seeds and both parameter values.
- [x] Implement `audit.py` with a new-output-directory requirement, exact witness,
  complete public/private episodes, per-setting outputs and hashes, and a finite
  census over seeds 0..7 and 50000..50007 with all four query rotations.
- [x] Run the census through the offline wrapper. Preserve failed runs honestly.
- [x] Write the README with exact portable commands, parameter definitions,
  source hashes, measured scope and limitations. Report evidence to the parent.

No commit is planned: this extracted packet has no Git metadata. All authored
paths remain inside the assigned parametric workspace, its focused test, and
`WORK/checks/parametric/`.
