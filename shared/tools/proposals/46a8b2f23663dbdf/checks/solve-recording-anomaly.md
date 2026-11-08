# Solve-recording filesystem anomaly

**Status: observed restoration of stale public solve artifacts; cause undetermined.** This concerns recording integrity, not a failed solution or masked-query result. No private labels, private scores, reference rule, or generator implementation were inspected for this investigation. Framework and `.review` files were not modified.

## Observed sequence

1. The completed older solve was bound to generator SHA-256 `2cec2f6f29ea427ef6e770f2ad530dfe7cdc781e6766ee94558dfd5592d175b1`. The root reviewer retained it under `checks/prior-solve/source-2cec2f6f/` and moved the active directory to `/workspace/scratch/e99e6bfff21b/old-solve-2cec2f6f`. Move and prepare were sequentially awaited, separate `exec_command` calls.
2. Preparation wrote a challenge and summary bound to the final generator SHA-256 `2b77752aa819ff3d2e1b5214f698055365f4ed747cd083baed087d97751fe67f`, but old `attempts/0001/` and `FINISHED_NOTES.md` reappeared. A genuine final-source check was numbered `0002`; finish refused to overwrite the existing notes snapshot. Independent inspection saw a mixed directory with final-source summary, status `attempted`, and `attempt_count: 2`. Its stale `FINISHED_NOTES.md` matched both retained older copies exactly: SHA-256 `399f009afbf21d474243fa9af7fd1184d0d3a430faac4845524b4b5aa4e11062`. The copies had distinct inodes and the same old modification time; no involved directory was a symlink.
3. The root reviewer then used atomic `os.rename`, asserted that the source directory was absent, and ran preparation inside one subprocess. That call reported only the five fresh files: `README.md`, `SOLVE_NOTES.md`, `challenge.json`, `solution.py`, `summary.json`. An independent subsequent read also saw `status: prepared`, `attempt_count: 0`, final generator hash, instance hash `e3a4966786c9f3cab1a34110b02ee40e09270ca35443ec0d3c11b2516da185dd`, and no `attempts/0001/report.json` or `attempts/0002/report.json`.
4. The root reviewer subsequently observed old attempt files again between `exec_command` calls, before any solve-file edit. This establishes the reported recurrence across tool boundaries. It does **not** establish which process, filesystem component, or synchronization mechanism restored the files.

## Code inspection and limits

`review_solve.prepare_solve` is not a reset operation. When no active summary exists, it creates/reuses the directory, writes the new challenge/summary, and preserves preexisting attempts and final notes. It contains no operation that restores an old attempt tree. `check_solve` derives the next revision from existing numbered directories; `finish_solve` opens `FINISHED_NOTES.md` exclusively. Those behaviors explain numbering `0002` and the finish error once stale artifacts exist. The return validator also checks each attempt's generator and instance hashes, so merely deleting old final notes would leave an invalid mixed-source episode.

No live-solve restoration path was found in the inspected wrappers, Racket setup, or runtime checkpoint restoration. The inspected solve-related repository tests use synthetic packets under `tmp_path`. A full repository pytest process was active during initial investigation, but no evidence identifies it as the restoring writer. Filesystem or tool-boundary synchronization remains an unproved hypothesis.

## Evidence-preserving recovery

The root reviewer retained mixed recording attempts under `checks/prior-solve/source-2b777-recording-failure/`. The chosen recovery executes archive, clean prepare, writing the final-source solution/work log, actual checks, and finish within one subprocess. Repeated checks of the same algorithm are explicitly bookkeeping re-verification, not independently discovered solutions or fabricated failures. Final episode identity and the final recorded source hash still require validation after the call and during return packaging. Recovery outcome is recorded in the final solve receipts, not asserted by this investigation note.

A useful shared-tool improvement would reject stale attempts or final notes when preparing a directory without a matching summary, and provide an explicit archive-and-reprepare operation with integrity checks. This is a proposal; no framework change was applied.

## Subsequent recovery observations

The root reviewer reported that a rename-based attempt left a ghost empty `0002` directory, and changed recovery to an explicit `copytree` archive followed by `shutil.rmtree` of the active solve directory. The complete prepare/write/check/check/finish lifecycle then ran in one subprocess. `checks/final-solve-commands.json` records the actual checks. The root's within-call verification found a finished summary and two reports, both bound to the final generator and instance.

The independent post-call verification confirmed `status: finished`, `attempt_count: 2`, final generator hash `2b77752aa819ff3d2e1b5214f698055365f4ed747cd083baed087d97751fe67f`, and instance hash `e3a4966786c9f3cab1a34110b02ee40e09270ca35443ec0d3c11b2516da185dd`. Reports `0001` and `0002` each had those identities and completed with `3/3` visible examples passing. However, that same read also found a third report, `attempts/0003/report.json`, with revision `3` and the same final identities. The exact-two-report assertion therefore **failed**. This was reported immediately; no solve artifacts were changed by the independent reviewer.

The root will perform the final clean recording and packaging after all agents stop filesystem activity, and verify the resulting episode separately. **This note does not certify current final solve consistency.** Concurrent snapshot synchronization remains an unproved possible explanation; no restoring actor or mechanism has been established. The final source-bound solve and packaging receipts determine the delivered outcome.

## Requested pytest interruption

The root reviewer authorized SIGINT only to owned pytest PID `19770`, after confirming its exact command. At attempted verification `/proc/19770/cmdline` no longer existed. A subsequent read-only process scan found no process with the expected command `/workspace/scratch/e99e6bfff21b/packet/WORK/.venv/bin/python -m pytest -q --tb=short`. **No signal was sent.** The owning root session retains the repository-suite stdout and terminal outcome.

## Final cleanup after parallel work stopped

All other agents stopped filesystem activity. The root copied the late-reappeared 0003 attempt byte-for-byte to checks/prior-solve/late-reappeared-attempts/0003, explicitly removed that extra directory, and verified exactly the two reports declared by the finished summary. Both remaining reports have the final source/instance, ordered revision numbers, and 3/3 visible passes. checks/final-solve-binding.json records this check. This cleanup does not change the actual two final checks or their frozen notes and makes no claim about the restoration mechanism.
