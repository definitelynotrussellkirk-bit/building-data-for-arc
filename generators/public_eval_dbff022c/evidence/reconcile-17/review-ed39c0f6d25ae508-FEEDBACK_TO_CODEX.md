# Reusable reviewer tooling

## Keep native test snapshots out of compact returns

The current public-task test runner writes a complete isolated runtime under
`checks/TASK/family-tests*/runtime`. The native return builder includes the
checks tree, so those useful local snapshots become copied runtimes in the
return and consume its expanded-byte budget. This conflicts with the packet's
explicit compact-delta requirement. Removing them in an earlier tool process
was also unreliable in this workspace: previously materialized files could
reappear when another payload started.

Implemented `checks/tools/package_delta.py` as a narrowly scoped wrapper around
the **unchanged** native `arcpuzzles.review_full_return.build_full_return`.
It recognizes native stages from their result and source-binding schemas,
verifies the exact snapshot inventory and bytes, preserves test reports and
bindings, and renames verified snapshots and generated caches to a new
packet-local stash outside checks. Because original paths were observed being
materialized again even during a same-process build, it now creates a fresh
work view under that stash. Every retained file has an independent copy with
verified hash, size and mode; complete source/destination inventories are
compared. Unexpected source and evidence files are retained for native
validation, rather than silently filtered. The original and copied checks both
receive the exclusions and compact view-binding receipts.

The unchanged native builder receives this fresh view. Its source validation,
archive budgets and approval boundaries stay intact. The wrapper rejects
changed bytes, symlinks, unsafe destinations and stale output paths; a failure
leaves its stashed bytes and view recoverable.

Thirty-two focused orchestration/refusal/recovery/archive/copy tests pass. They use
synthetic snapshots, real ZIP fixtures and explicitly labeled mock builders.
Because copied files were observed reappearing during one packaging attempt,
native success now also requires a postflight scan of the actual ZIP and native
evidence manifest. Any `runtime` path component under checks or generated cache
component causes rejection, including a retry with an empty cleanup plan. The
ZIP and stashes are preserved on rejection. Run final packaging without other
processes inspecting or materializing the staged snapshots.

The final packet build is the
separate native integration check; its result and exclusions receipt are not
replaced by those unit tests. Three independently reviewed wrapper defects
received failing regressions before their fixes. The source and tests are
included for future agents to reuse. Owner integration into the shared packager
is a proposed follow-up, not a shared-runtime change made by this return.

## Preserve full audit evidence with compact JSON

`checks/tools/finite_rival_audit.py` now writes compact grid-heavy episode and
harmful-case JSON while keeping the summary readable. It drops no programs,
grids, predictions, query executions or source bindings. A focused round-trip
fixture reduces grid artifacts from 3,700,004 to 415,398 bytes (88.8%); the
complete fixture audit shrinks from 3,709,448 to 424,842 bytes. Unicode and CRLF
program bytes, every query prediction and both harmful cases are retained.

The current helper suite passes 61 tests; the packaging wrapper separately
passes 32 tests. These are distinct recorded runs. The earlier 16- and 25-test
wrapper results remain historical evidence. Mock finite-audit fixtures prove orchestration and serialization;
the assigned-family reports supply actual protected Racket execution evidence.
Current source hashes, exact commands, red/green receipts and limits are in
`checks/tools/validation.json` and `checks/tools/README.md`.

No allocation, approval, runtime, raw-data, publication or training policy was
changed. These improvements make the existing review workflow easier to run and
transport without weakening its checks.

## Check native return metadata before packaging

The first native packaging attempts caught two transport-format mistakes in the
return metadata: task-local deliverable paths lacked the `repo/` prefix, and
command working directories were absolute. Both are corrected; no family code
or label needed changing. The exact original command receipts remain intact.

The reusable `checks/final-review/check_release.py` now applies the unchanged
native `validate_target_outcomes` and `_intake_summary` gates before packaging,
in addition to its source/evidence consistency checks. Ten pure metadata tests
cover the valid return, each of the six missing-prefix mutations, an absolute
command directory, and protection of an existing report. Reports use a fresh
explicit `--out` path so earlier evidence is never overwritten.

For future packet instructions, distinguish these two path bases explicitly:

| Field | Path base and example |
| --- | --- |
| `RESULTS.json` prototype/promotion/inventory paths | Relative to WORK: `repo/generators/TASK/workspace/parametric/...` |
| `promotion.json` adapter/resources | Relative to the repository: `generators/TASK/workspace/parametric/...` |
| Verification command `cwd` | Packet-relative, normally `repo`; the command receipt retains its original absolute environment. |
