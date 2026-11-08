# Working notes: f812a7b32f47

## Current parametric extension — October 24, 2026

`workspace/parametric/adapter.py` proposes `selection=all|largest` with matched
input streams, 2–6 demos and 1–4 queries. `all` retains the exact canonical
Racket bytes. The separate shared grammar adds preexisting interior 7 fragments;
`largest` completes crossings, then retains every co-largest four-neighbor
orange component and clears all losing orange cells, including original fragments.
The production generator and selected reference are unchanged.

The empty-interior proposal was rejected because its components factor into
independent marker runs. Added fragments make completion merge components and
reverse the original size ranking. The retained causal witness compares the
qualified rule with selecting before filling and skipping completion.

Self-review found that two original demos both had size-8 winners, letting a
fixed size cutoff fit them and miss a size-3 query. The repaired lesson keeps an
8-cell winner in the first demo and two 12-cell winners while discarding size9
in the second. `checks/f812a7b32f47/threshold-counterexample.json` retains the
original protected-Racket witness; the final audit tests both exact8 and cutoff8
alongside the existing finite rivals. Only the finite tested alternatives are
covered. Four queries include the genuine 5×6 minimum and dense 30×30 completion.

Replay, export and owner handoff commands are in the parametric README. Native
reviewer qualification is supplied separately from exact-source owner acceptance;
the next owner action is integrated-source qualification and acceptance, with no
training activation implied.

## Review 2026-10-03

The selected Racket rule is edge-specific: compute the nonzero bbox, read color-2 row markers from the interior of its left edge and color-3 column markers from the interior of its top edge, then fill their crossings with 7. Canonical train pair 2 contains a color-2 bottom-left corner; corners are not scanned by the authority, so the old validator's rejection was incorrect.

The strongest plausible rival that fits all five canonical pairs is a corner-special-cased anywhere-marker rule: use every non-corner row containing 2 and every non-corner column containing 3. Version 4 refutes it in every ordinary draw with one to four lawful bottom-edge 2 / right-edge 3 distractors.

Public controls were reduced to six exact pixel-observable axes. `observe_overrides` recovers each realized value; unknown, mistyped, and out-of-domain requests reject before drawing. The independent workspace probe checks canonical parity, distribution support, and intended-versus-rival disagreement without importing production rule helpers.

Test-first evidence is retained under `checks/`: corrected baseline red 31 failed / 14 passed; lesson-minimum red 1 failed / 45 passed; final task tests 46 passed. Final generator SHA-256: `a4d7c0b080c3c9f13cc23d2dd02ec0c180b7349cd8b8d7ed52519ff35e600969`.
## Current reviewer considerations

Source SHA-256: `a4d7c0b080c3c9f13cc23d2dd02ec0c180b7349cd8b8d7ed52519ff35e600969`.

# Decisions for `f812a7b32f47`

## D1 — Treat the selected Racket rule as immutable authority

**Input choice.** Preserve the canonical transformation exactly: bbox-left `2` cells select rows, bbox-top `3` cells select columns, and their interior intersections become `7`.

**Original rationale.** The baseline notes did not record a precise rationale; the source broadly described frame intersections. Direct canonical/Racket comparison established the edge-specific rule and exposed the bottom-left color-`2` corner quirk.

**Alternatives considered.** A literal “all `2` rows × all `3` columns” rule and a corner-special-cased “non-corner markers anywhere” rule were both tested. The literal rule is already contradicted by one canonical corner, while the stronger non-corner rival fits all five canonical pairs.

**Probe and failure mode.** `workspace/reference_probe.py` implements the intended rule and rival independently. `checks/independent-audit-final.json` shows 5/5 canonical oracle matches and a legal explicit disagreement witness.

**Limit.** Canonical/Racket authority was not changed; this is generator repair, not task reinterpretation.

## D2 — Use one hollow nonzero frame as the complete ordinary grammar

**Input choice.** Draw a rectangular hollow frame on background `0`, with all markers on its border and an empty interior.

**Rationale.** This makes the nonzero bbox explicit, matches the canonical visual family, and makes every validity condition independently checkable. Floating placement and canvas padding vary separately through layout RNG rather than being advertised as false semantic axes.

**Rejected alternative.** Retaining generic `offset`, `position_bias`, `density`, `texture`, or fixed color-count declarations. Those baseline fields were singleton, dead, overlapping with negative fixtures, or not recoverable from pixels.

**Probe and failure mode.** Destructive regression tests break the border, add interior noise, erase marker classes, make the grid ragged, or inject invalid colors; `self_check` rejects each mutation.

**Limit.** Nonrectangular frames and interior objects are outside the ordinary generated domain. This is intentional and declared rather than silently implied.

## D3 — Advertise only six exact observable axes

**Input choice.** `frame_h=5..13`, `frame_w=6..15`, `frame_color∈{1,4,5,6,8,9}`, `n_top=1..4`, `n_left=1..3`, and `n_distractors=1..4`.

**Rationale.** Each value changes visible pixels and can be recovered exactly by `observe_overrides`. Domains are broad enough to include canonical-scale examples and all difficulty bands while respecting marker capacity.

**Alternatives considered.** Difficulty-local legal ranges would have made globally advertised boundary overrides fail; non-semantic layout descriptors would not have been reliably observable. Both were rejected.

**Probe and failure mode.** The final override stage checks the matrix and unknown-key policy. Task tests round-trip every legal value, reject bools/non-integers/out-of-range values, and sample full support. The independent 768-draw probe observed every domain value in each band.

**Limit.** Difficulty affects default weights, not legality. Explicit overrides remain exact across all bands.

## D4 — Make off-axis marker distractors mandatory

**Input choice.** Every ordinary instance contains one to four color-`2` cells on the bottom bbox edge and/or color-`3` cells on the right bbox edge.

**Rationale.** These cells are lawful and inert under the authority, but they force the learner to use the correct **edge** rather than marker color alone. Mandatory inclusion makes each instance, not merely the aggregate distribution, a witness against the strongest canonical-fitting rival.

**Alternatives considered.** Optional distractors were simpler but allowed non-discriminative lessons. Interior distractors would violate the frame grammar. Corner-only distractors would not refute the corner-special-cased rival. Bottom/right border distractors are the smallest lawful distinguishing construction.

**Probe and failure mode.** The explicit witness in `QUESTION_ANSWER.md` differs at five cells. Across 768 independent draws, intended and rival outputs disagreed 768 times; across the source-bound census, all 300 lessons refuted all declared rival aliases.

**Limit.** A solver could still memorize this generator’s presentation. The result specifically addresses semantic identifiability of the edge rule, not every possible stylistic shortcut.

## D5 — Accept the canonical bottom-left marker quirk without weakening validation

**Input choice.** `self_check` permits marker colors at bbox corners while requiring every non-corner border cell to be frame color or the edge-appropriate marker/distractor color.

**Rationale.** One canonical input has color `2` at the bottom-left bbox corner, yet the authority only scans interior rows/columns. Rejecting that input was a validator defect.

**Alternative considered.** Special-case only that exact canonical grid. Rejected because it would encode an example rather than the grammar.

**Probe and failure mode.** All five canonical inputs pass, while broken borders and illegal interior cells still fail. Canonical acceptance is measured both by the battery and independent probe.

**Limit.** Corner marker colors remain semantically inert; the generator itself does not need to emit them because bottom/right non-corner distractors are stronger teaching witnesses.

## D6 — Require two demonstrations per lesson

**Input choice.** Set `EXAMPLES_NEEDED=2`, with one query.

**Rationale.** A one-demonstration lesson-identifiability audit was formally weak and triggered the semantic gate’s vacuity warning even though individual instances were discriminative.

**TDD record.** The regression test `test_lesson_contract_uses_at_least_two_demonstrations` failed at `1` in `checks/task-tests-red-lesson-min/`, then passed after the minimal constant change. The semantic gate subsequently passed.

**Limit.** Two examples are not claimed to be mathematically minimal for every hypothetical rival; they are the smallest non-vacuous contract used by the shared census.

## D7 — Keep an independent oracle/probe beside production

**Input choice.** Add `workspace/reference_probe.py` without importing production rule helpers.

**Rationale.** This gives future reviewers a reusable way to check canonical parity, recover observable axes, sample support, and compare the intended rule with the declared rival. It avoids circular tests that merely call the implementation under review.

**Alternative considered.** Rely only on shared battery stages. Rejected because a task-local exact witness and independent oracle make the semantic claim easier to replay and inspect.

**Limit.** The probe is supplementary. Racket remains the label authority, and source-bound shared checks remain the acceptance gate.

## D8 — Preserve failures and interrupted evidence

**Input choice.** Retain the flawed first red suite, corrected red suite, lesson-minimum red test, initial semantic warning, incomplete baseline attempt, and timed-out repository pytest log.

**Rationale.** These records distinguish genuine discovery from a post-hoc passing narrative and prevent interrupted infrastructure runs from being mislabeled as task failures.

**Limit.** The first task-test red suite used a too-weak literal rival and is not the final semantic claim; `checks/task-tests-red-v2/` is the corrected baseline evidence.
