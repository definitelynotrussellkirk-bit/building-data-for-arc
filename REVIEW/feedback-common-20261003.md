# Review queue cleared — October 3, 2026

The live receipt scan after batch34 has **260 return versions: 245 accepted,
15 deferred, zero unread and zero needs-evidence intake decisions**. These are
intake dispositions, not generator certification or training admission.

This pass accepted 39 older queued returns, two previously held candidates,
and fourteen new returns. Nine older versions were read and superseded: eight by
later revisions of the same assignment, one by a stronger independent repair.
The six previously deferred versions remain explicit decisions. All original
ZIPs, findings, audits and solve records remain retained. Operational receipts
are in `var/review/incoming/20261003-backlog/` and
`var/review/incoming/20261003-batch34/`; per-assignment decisions are in
`REVIEW/assignments/` and selected-file hashes in each generator's `evidence/`.

Ordinary repairs use the owner's brief-review, reviewer-reported policy. No
routine battery or private solve replay was run. The conflicting repairs of
`056999828b88` were combined as v6.1.0 and checked with 21 focused portable tests.
The first merge exposed two failures, fixed by keeping the existing geometry
witness separate from the new shared-color witness and updating the probe.
The final passing log is retained; the first full log was overwritten, so its
failure summary is recorded without claiming the original log survives.

## Common requests, in priority order

These are recurring themes from the briefs and general feedback, not vote
counts. Repeated rounds of one assignment are not independent endorsements.
This document is the shared tooling worklist. The implemented subset is listed
below; the remaining proposals are not completion claims.

## Implemented from this feedback

- `check --stage task_tests`: one portable test command, new task/workspace
  dependencies and frozen fixtures, source hashes, and an explicit no-tests
  outcome. No extra thirteenth stage was added to the normal battery.
- Incremental `check --out` receipts: initial running manifest, stage checkpoints,
  evidence hashes, progress log and interrupted outcome. Controlled interruption
  stops the child process group; automatic resume remains future work.
- Correct Git patch EOF handling in the return builder, prompted by
  `review-16368c6e8812a1c1`. Tests apply generated patches with actual Git and
  compare exact bytes, including CRLF, bare CR and Unicode separators.

The new packet documents the portable command and checkpoint behavior. Its
return format remains compatible with older packets.

1. **Check assembled lessons, not just isolated grids.** Exercise the actual
   public sampler, all cyclic starts and at least 100 lessons per band where
   justified. Record unique inputs separately from overlapping windows. A
   wrong rule must fit the original canonical examples before it is a useful
   rival; distinguish surviving demonstration rules from query disagreement.
   Composed rivals, independent spatial rivals and observable negative controls
   repeatedly exposed shortcuts despite green batteries. Representative returns:
   `review-d914c056785610b1`, `review-361d29beeb4e7c05`,
   `review-18dc4ac2517ff627`, `review-083504bc1ff4c2ff`.
2. **Give reviewers one portable task-test command.** Discover task-local tests,
   stage their workspace dependencies, and record actual source/destination
   hashes. Root pytest does not establish that task-local tests ran. State the
   exact runtime/bootstrap command and separate installed-wheel checks from
   source-layout checks. Representative returns: `review-c75b3c20a8a6e96a`,
   `review-ecb9eab7828409d2`, `review-201ae2dcbb09941c`.
3. **Persist check evidence as each stage finishes.** Write stage receipts to
   the caller's output directory with source identity, exit status and progress;
   permit resuming interrupted long checks. An interrupted wrapper should not
   discard completed stages or relabel them as semantic failures. Representative
   returns: `review-ecb9eab7828409d2`, `review-23535e20aa5b9a08`,
   `review-9d4f800edf4b72c2`.
4. **Make overrides describe observable postconditions.** Verify requested
   counts against returned grids; document unknown/degenerate behavior and
   reference-runtime validity. Separate canonical input acceptance from a narrow
   teaching curriculum. Test coupled geometry/palette controls and actual
   per-band support. Representative returns: `review-d914c056785610b1`,
   `review-0c3255d49c88983e`, `review-43bfa46e57f55f67`.
5. **Keep evidence compact and lint actionable.** Deduplicate large success
   ledgers by content hash, group failures by cause and retain minimized
   reproducers. Scope reserved-name warnings to actual bindings. A short
   subprocess test must distinguish interpreter startup from streaming; do not
   globally inflate timeouts to hide that distinction. Suppress terminal-control
   output in non-TTY runs (`review-c0b2c1c20021d9d8`).
6. **Make selected-authority divergence repairable without erasing history.**
   Report exact selected files, JSON fields and canonical hashes; offer an
   opt-in, task-scoped patch. Preserve original source representations and the
   canonical ledger. `review-2039f1d410b22dbf` independently repeated this request.
   Its generator/tests/notes were accepted; cached solution text normalization
   was deferred, so its reported full-candidate battery is not a fresh check of
   the selected live combination. The same exclusion applies to the latest
   `review-2c6a6bb78f6b9f5d` return.
7. **Bind evidence to executed bytes and explicit solve exposure.** Use the
   existing public reference-apply interface, record patch readback and actual
   staged hashes, and carry generator/instance/rule versions with work logs.
   Keep exposed and blind solves distinct. New imported solves remain unknown
   until independently scored; visible-example success is not a private score.

## Concrete follow-ups retained after acceptance

| Task | Remaining evidence or question |
|---|---|
| `5ccdbe078da6` | Reviewer reports 24/60 ambiguous default lesson windows; candidate acceptance does not resolve this. |
| `ee64b9b0fe20` | R7 frame retention and query-only branch evidence need follow-up. |
| `93e709ad4848` | Reported 11 green stages and one minimal-impostor gate failure; lawful singletons/lines are task-specific counterevidence, not an all-green result. |
| `17b682bce66f` | Collision behavior is unidentified by the visible lesson: four surviving policies, two query predictions. |
| `f7c20cfd443f` | Prior singleton-impostor lint failure retained; singleton seeds are part of the intended grammar. |
| `0b999a8ea028` | Prior canonical max-object support and identical-band failures retained; no new passing battery claimed. |
| `84def340ce03` | New return reports 10 green / 2 failed mutation-sensitivity gates; lawful even-grid mutations have reference counterevidence. Candidate accepted, gates unchanged. |

The outgoing packet retains the short acceptance brief and reviewer-owned fresh
delta replay, source hashes, focused checks, two audits and solve notes. This
refresh changes its library, tooling instructions and retained evidence, not its
return format.

## Shared tooling qualification

19 focused regressions passed; the real portable command passed all 85 tests on
`9900de625ddd`. The broader suite with explicit system Racket passed 248 tests
and failed three optional tensor-export tests: its parent sees user-site Torch,
while isolated children deliberately disable user-site packages. Rechecking the
affected tests and new runtime checks with user-site disabled consistently gave
21 passes and three explicit Torch skips. The earlier unpinned run (230 passes,
21 failures) and all failing test names remain in
`var/review/incoming/20261003-batch34/tooling-qualification.json` and its logs.
No full-suite all-green claim is made. No generator certification or learner
admission follows from these shared tooling checks.
