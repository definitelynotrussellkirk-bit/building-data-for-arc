# Exact-delta replay and optional proposal verification

## Completed results

The original uploaded ZIP was independently extracted at
`/workspace/scratch/df8d9659f825/fresh-replay`. Its verified Git root is that
outer directory; the working directory for packet commands is its `WORK/`.

| Check | Result | Evidence |
|---|---|---|
| Original extraction and independent Git root | Original ZIP hash and baseline generator match | `fresh-extraction.json` |
| Exact task delta | All eight changed files match expected after hashes | `task-patch-replay.json`, `expected-source-files.json` |
| Relocated task regression stage | 30 passed; no failures, errors or skips | `fresh-task-tests-final/`, `fresh-task-tests-final-command.json` |
| Optional authority proposal | Both original/patched guards pass; only the two intended fields change | `authority-patch-application.json` |
| Fresh source plus authority proposal | Full 12-stage battery green, including Racket execution parity | `fresh-with-authority-battery/`, `fresh-with-authority-command.json` |
| Final standalone replay helper | Five guard/application cases pass | `helper-regressions-final/summary.json` |

The task generator remains
`fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6`.
The separate formatting patch remains
`1ae81345902af035aa24ff461d62f1045afdc483a64ac1e16e7fb6e7be2e93e5`.
The finished post-repair solve binds those same generator bytes. The task
patch SHA and every modified-file hash are recorded in
`expected-source-files.json`; the final archive's task patch must match them.

The fresh task-test stage used the packet wrapper from the fresh `WORK/`
and the explicitly recorded venv for both wrapper and payload. Its actual
portable runtime was `/tmp/arcpuzzles-check-1r90yjjc`. No installed environment,
full runtime, or duplicate repository is included in the return.

## Restore the evidence

The packager bundles `checks/` to keep the outer ZIP small. After extracting
the return ZIP into its own directory, restore all original evidence paths:

```sh
tar -xzf EVIDENCE-BUNDLE.tar.gz
```

`EVIDENCE-BUNDLE.json` contains the compressed archive hash and each original
file's path, expanded size and SHA-256. The package builder validates that
manifest and the total expanded-size budget. This is lossless bundling; failed
attempts and large census instances have not been dropped.

## Apply the task delta to another fresh original packet

The following is a usage template; the exact commands actually run are in
`RESULTS.json` and the receipts. Initialize a Git root in the new outer
extraction, then run the helper from the extracted return directory:

```sh
git init -q /path/to/fresh-packet
python3 checks/return-validation/apply_verified_delta.py \
  --workspace /path/to/fresh-packet/WORK \
  --git-root /path/to/fresh-packet \
  --patch patches/source.patch \
  --expected-files checks/return-validation/expected-source-files.json \
  --receipt /path/to/receipts/task-delta.json
```

Use a new receipt path outside the target `WORK/repo` source tree. The helper
requires the intended Git root, verifies the reviewed patch hash and original
file bytes, derives the Git prefix, rejects skipped patches, and verifies all
resulting bytes. It deliberately accepts this task-only delta, not the separate
shared proposals. It refuses repeat application instead of assuming it is safe.

Then use the packet's normal supported task-test command from the fresh
`WORK/`, supplying the same Python interpreter to wrapper and payload as
described by the existing test preflight. The recorded command and dependency
versions are in `fresh-task-tests-final-command.json` and its result manifest.

## Optional shared proposals

The authority patch has paths relative to `WORK/repo`, not `WORK`. Run the
original/patched checks described in `../authority-proposal/README.md`. If the
Git root is the outer packet directory as in this replay, both `git apply`
commands require `--directory=WORK/repo`. If the Git root is `WORK/repo`
itself, no directory prefix is needed. Both cases still require the proposal's
whole-file hash guards. The actual prefix and successful commands are retained
in `authority-patch-application.json`.

The independent process-liveness proposal is in
`../process-liveness-proposal/`. It was tested in another small isolated
workspace, not applied to either the main review or this fresh task/authority
copy. Its 33 focused tests are separate from the 30 generator tests and the
12-stage battery.

## Failures retained and what they mean

- The first package attempt rejected a frozen task-evidence-index edit. The
  original index was restored; proposed audit dispositions are separate in
  `../resolution-proposal/`. Both package receipts are retained.
- The first direct Git replay exited zero while skipping all patch paths.
  The missing-file verification failed, and the subsequent task-test attempt
  returned `no_tests`. See `task-patch-replay-failed-01.json`,
  `git-subdirectory-diagnostic.json`, and `fresh-task-tests/`. These are not
  passing checks.
- The first four helper checks passed, but independent review found a receipt
  path could overwrite a newly applied source file. The new regression
  reproduced that failure before the guard was added. The actual failing
  helper is `apply_verified_delta_receipt_bug.py`; `helper-receipt-red/`
  retains the failure and unexpected receipt. The final helper prohibits
  receipts in the source tree and uses exclusive creation; all five cases pass.

No failed solve was fabricated, no test fixture was changed to make the main
suite green, and neither shared proposal is silently included in the task delta.
