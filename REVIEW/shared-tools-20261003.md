# Shared reviewer tools — October 3, 2026

The owner requested an Astra implementation of recurring tooling suggestions.
The shared lesson census and portable canonical-data helpers are integrated in
ARCpuzzles. The reviewer ZIP exposes their commands in WELCOME and DUTIES; it
keeps the existing return format and lightweight maintainer intake policy.

## Delivered

- `arcpuzzles lesson-census ID`: production materialization through the actual
  Racket authority, dynamic declared-rival checks, canonical-fit results, exact
  instances and source hashes, replay seeds, unique-input and per-band counts.
- Checkpoints after every completed lesson. Timeout or inconsistent worker
  termination retains partial evidence as an error, rather than a completed run.
- Separate results for rivals refuted by demonstrations, agreeing everywhere,
  fitting demonstrations but disagreeing on queries, and execution errors.
- `reviewer_support.canonical_pairs` and `find_root`: portable test-authoring
  access without guessed canonical-data paths or neighboring checkouts.
- Wrapper help and effective-working-directory diagnostics, with absolute
  repository import paths and `ARCPUZZLES_HOME` binding.

Usage and limits: [shared tools](../shared/README.md). The helper exposes answers;
reviewers must keep it closed during both visible-only solve stages.

## Exercised

- 29 focused census, wrapper, packet and assignment tests passed.
- Astra's real Racket smoke: 18 lessons, 72 pairs, 71 unique inputs; all six
  requested start residues in each difficulty band, no measured ambiguity or
  execution error on `ebff81ea3252`.
- Independent extracted-packet check: offline Racket setup, random assignment,
  helper import/canonical read, and the documented census command passed from a
  relocated directory with spaces. Six lessons / 24 pairs completed across all
  three bands. Source/member verification covered all 29,760 manifest members,
  including 268 approval receipts.

Exact evidence is retained under
`var/review/tooling-qualification/shared-tools-20261003/`: `qualification.json`,
command logs, the extracted census report and the untouched Astra smoke report.
Packet identity is in `full-packet-current.json` and its immutable cache receipt.

These are shared-interface measurements, not new generator certifications or
private solve scores. The census currently supports per-puzzle generators and
finite declared rivals. Requested start-residue coverage is not cyclic query
rotation; custom probes remain necessary for cyclic queries, legal joint axis
support or additional plausible rivals. Automatic battery resume remains open.
No optimizer run or trajectory admission was performed.
