# Parametric rectangle frame prototype implementation plan

**Goal:** A task-local proposed extension with two episode-fixed parameters, matching Racket, identifiable demonstrations and four distinct queries.

**Architecture:** Keep four exact Racket sources alongside a standalone Python episode sampler. The canonical source is copied byte-for-byte from the assigned canonical record. Execute all labels and declared rival predictions through the included Racket bridge. Export public challenges and private source-bound receipts separately.

**Tech stack:** Python 3.12 standard library and the repository's RacketBridge; no new dependencies.

**Spec:** WORK/PARAMETRIC-RULES.md and WORK/ARC-DESIGN.md.

## Global constraints

- Changes only in this prototype directory and the new task-local test file.
- center_extension: false or true; stroke_width: 1 or 2. Original setting: true, 1.
- Nonzero connected filled rectangles, local majority frame and local minority strokes remain invariant.
- Every output executes the matching Racket source; Python never provides labels.
- Four distinct queries by default; demonstration and query counts separate.
- Public identities depend only on visible train inputs/outputs and query inputs.
- Proposed prototype only: no approval, admission, canonical API or shared runtime change.

## Task and checks

- [x] Write tests for literal four-setting outputs, exact canonical equivalence, episode reproducibility and demonstration-only rival discrimination, input/count validation, public redaction/identity and CLI export.
- [x] Run the tests before implementation; retain the expected missing-feature failure.
- [x] Materialize the canonical source plus three narrowly changed predicates, implement episode sampling, bounded validation and export.
- [x] Run focused tests through real Racket and retain the green result.
- [x] Export all four settings at seed 17 and retain complete private/public episodes, exact commands, source hashes and pairwise witnesses.
- [x] Document runnable commands and explicit limits. Parent reviewer owns the canonical battery.

## Review focus

Canonical byte drift, confounded settings, query answers leaking into inference or filenames, duplicate queries, and invalid parameter/count requests are covered by tests. Finite rivals are not proof against every possible alternative rule. The prototype deliberately has no production registration.
