# Shared reviewer tooling: query rotation and test receipts

Implemented at the owner’s request to act on accumulated reviewer feedback.
Use the same sendable ZIP; WELCOME now shows the new commands.

## Delivered

- `lesson-census --rotate-query`: with one query, hold out every labelled pair
  once, preserve remaining pair order, and score all declared rivals/hooks.
  Each rotation retains query/train indices, statuses, warnings and errors next
  to its exact source instance. Pure deterministic predictions are cached, so
  query rotation requires no additional generation or Racket label calls.
- Top-level summary: production ambiguity and rotated ambiguity counted
  separately; materialization and scoring errors, hook warnings, pair/unique
  input counts and rotations remain distinct. `no_ambiguity_found` describes
  sampled finite-rival results. Canonical read failures now propagate to error.
- Nonblocking task-test AST diagnostics: private `scripts.*` imports explain
  why direct packet pytest fails and name portable helpers/public APIs.
  Legacy staged tests remain usable. `reviewer_support` imports work in the
  staged task-test subprocess as well as through the packet wrapper.
- Task-test JUnit evidence and structured counts for tests/passed/failed/errors/
  skipped. Missing or interrupted XML remains unknown rather than zero errors.

Usage: [shared tools](../shared/README.md), [verification](../docs/verification.md).
All tools remain authoring-only: reference answers stay closed during solves.

## Measured

- TDD: eight missing-behavior failures, then 31 focused passes.
- Complete public repository suite: 288 passed in 148.52 seconds.
- Extracted-packet Racket smoke on existing task `ebff81ea3252`: two
  materialized lessons, eight labelled pairs and eight query rotations. No
  measured ambiguity or execution error. It ran the packet’s code from a
  temporary extracted directory using the project Python environment; it is
  not a new independent installed-environment qualification.
- Tested packet `e3162adce1655cd358d6e5e970a634cb0e6b87da9567c13a169007b04fde85ba`: all 30,287 manifest members hash-verified.
  Batch 73’s newer packet preserves these shared tool/smoke-task sources exactly;
  its full archive verification is recorded separately in the current handoff.

Receipt/logs/report: `var/review/tooling-qualification/query-rotation-20261003/`.
Packet identity is in full-packet-current.json. Shared-tool execution is separate
from reviewer-reported repair acceptance and private solve scoring.

## Open

Rotation reuses a materialized bundle. It is not exhaustive cyclic-window
coverage, proof of lesson identifiability, or a replacement for independent
new rivals, topology/diversity probes and joint-axis tests. Deterministic rival
functions are required. Automatic battery resume, fail-fast override enumeration,
false CANONICAL_SHORTCUT claim enforcement and general evidence dedup remain
separate follow-ups. No optimizer or trajectory training admission was run.
