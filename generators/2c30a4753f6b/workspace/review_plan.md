# Reflection family review plan

**Goal:** deliver a runnable four-setting parametric reflection prototype and
repair measured canonical sampling/test defects without changing the authority.
**Spec:** packet `DUTIES.md`, `PARAMETRIC-RULES.md`, and `RETURN-GUIDE.md`.
**Architecture:** keep variants in `workspace/parametric`; keep canonical labels
bound to the selected Racket rule. Add source-local finite rival contracts and
an alternating witness/ordinary schedule, retaining every profile override.
**Runtime:** Python 3.12+, NumPy, Pillow, pytest, bundled Racket 8.10.

## Tasks and verification

- [x] Finish blind visible-only solve before source inspection (3/3 visible).
- [x] Run baseline battery; retain scalar-validation failure and NO_CONTRACT.
- [x] Build parametric prototype first: axis/side fixed per episode, exact
  Racket labels, canonical parity, all-setting separation, public/private split.
- [x] Add failing regressions for strict seed/index types, canonical-fitting
  rivals, ambiguous three-demo lessons, query rotations, and large-grid support.
- [x] Repair scalar validation and schedule; migrate the allowed task-owned
  legacy test to portable helpers. Frozen/shared fixtures remain untouched.
- [x] Run focused tests, 100 lessons per band with all query rotations, and
  fixed-seed enumeration of the declared two-position schedule.
- [x] Run strict after battery and task tests against the final source.
  Measured result: 84 tests pass; strict battery 11/12 green, one lawful-line
  heuristic warning retained for maintainer adjudication.
- [x] Finish fresh post-repair solve, then perform two assigned audits.

Final handoff procedure: package the exact delta, replay it into a fresh runtime
closure, rerun focused tests there, and compare final patch bytes. The completed
execution status belongs in `WORK/REVIEW.md` and `WORK/RESULTS.json`, outside the
source patch, so packaging receipts do not change the tested source identity.

## Review focus

Reject Boolean/floating/string seeds and indices without silent coercion.
An overridden profile must remain honored even at a scheduled witness position.
Three demonstrations must refute size/color shortcuts before a query needs them.
Query rotation evidence must use accepted sample indices, including rejections.
Public prototype challenges must exclude parameters, program, and query labels.

## Rulings

The extraction is already isolated and contains no Git metadata; edit this
packet directly and use its official patch builder. The original archive is
unchanged. Task-test inspection confirmed that the old fixed-depth test is an
editable task-owned source, not an independent frozen root fixture.
