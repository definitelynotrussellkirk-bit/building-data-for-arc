# Finish a provisional ARCpuzzles recovery

A `RECOVERY_*.zip` is **not an official review response**. It preserves the
repair and its evidence when the original packet cannot be fully materialized.
`finish_recovery.py` rebuilds a fresh, complete copy of the exact original ZIP,
replays the fixed assignment and patch, runs checks, and invokes the original
unchanged `package_return.py`. Only a successful native build produces a
`review_response_*.zip`. Maintainer acceptance remains a separate decision.

The helper's execution tests use tiny synthetic packets. The full real packet
has **not** been replayed by this helper in the current constrained environment.

## Recovery directory layout

Paths are relative to the extracted recovery directory.

| Path | Purpose |
| --- | --- |
| `finish_recovery.py` | This standalone finalization helper. |
| `zip_capacity_preflight.py` | Required companion capacity checker. |
| `recovery.json` | Identity, hashes, reserves, and exact focused commands. |
| `source.patch` | Exact allowed task delta, in the native builder's patch format. |
| `contracts/ASSIGNMENT.json` | Original native repair assignment, unchanged. |
| `contracts/BLIND_ASSIGNMENT.json` | Original blind assignment, when assigned. |
| `contracts/AUDIT_ASSIGNMENT.json` | Original audit assignment, including its saved seed. |
| `provenance/scoped_extraction_receipt.json` | Original archive SHA from the extraction receipt. |
| `payload/REVIEW.md` | Repair brief and findings. |
| `payload/DECISIONS.md` | Preserved decisions. |
| `payload/QUESTION_ANSWER.md` | Answer to the assigned question. |
| `payload/FEEDBACK_TO_CODEX.md` | Shared-tool feedback. |
| `payload/AUDIT.md` | The assigned audit findings. |
| `payload/RESULTS.json` | Honest reported status and earlier command receipts. |
| `payload/checks/…` | Retained checks, failures, reproducers and receipts. |
| `payload/solve/…` | Unchanged post-repair public solve episode. |
| `payload/solve-blind/…` | Unchanged blind public solve episode. |

Do not include `.review` files, private labels, private scores, installed
environments, or a copied repository. Every regular file under `contracts/`,
`provenance/`, and `payload/` must appear in `recovery.json`'s `files` map.
Symlinks are rejected. Helper source, tests, this guide and verification evidence
may remain at the recovery directory's top level; they need not consume the
official return's evidence budget.

The helper reserves `payload/checks/recovery-finalization/` and
`payload/checks/recovery-task-tests/`; leave these paths absent.

## Manifest

Use schema `arcpuzzles-recovery-v1`. Required top-level fields are:

| Field | Value |
| --- | --- |
| `original_archive_sha256` | Full original ZIP SHA-256; must equal the preserved extraction receipt. |
| `patch_sha256` | SHA-256 of the exact `source.patch` bytes. |
| `final_generator_sha256` | SHA-256 of the final repaired generator. |
| `packet_id` | Original `ASSIGNMENT.json` packet ID. |
| `assignment_id` | Original assignment ID. |
| `task_id` | Original selected repair task ID. |
| `files` | Map of every contracts/provenance/payload relative file path to its lowercase SHA-256. |
| `focused_tests` | Nonempty list of exact command objects, as below. |

Optional `reserve_bytes` and `reserve_inodes` default to 536,870,912 bytes and
4,096 inodes beyond the extraction estimate. They are headroom estimates, not
reservations or guarantees. Raise them when the particular task needs more.

A focused command has a working directory of `WORK` or `WORK/repo`, a nonempty
argument array, and an optional positive `timeout_seconds` (default 900):

```json
{
  "cwd": "WORK",
  "argv": [
    "{python}", "-B", "run_with_racket.py", "{python}", "-B",
    "-m", "pytest", "-q",
    "generators/YOUR_TASK_ID/tests/test_generator_contract.py"
  ],
  "timeout_seconds": 900
}
```

Replace `YOUR_TASK_ID`; the exact argument `{python}` is replaced with the chosen
interpreter. Commands execute directly, without a shell. Review these commands
before using `--execute`: this is orchestration of trusted reviewer commands,
not a sandbox for arbitrary programs.

The original ZIP used in this review has SHA-256:

```text
c42d19cab9243976c5a31157abc0db284d9d66b1bb2dd33a90252bb1a4e5b266
```

## Plan, then execute

Place the original ZIP separately and choose an absent destination outside the
recovery bundle. Existing destinations, including empty directories, are refused.
The default command only checks metadata, identities, hashes and capacity:

```sh
python3 -B finish_recovery.py \
  --recovery /absolute/path/RECOVERY \
  --archive /absolute/path/original-review.zip \
  --destination /absolute/path/new-packet \
  --python /absolute/path/ready-environment/bin/python
```

Add `--execute` to carry out that plan. Use Python 3.12+ with pytest, NumPy and
Pillow available when `PYTHONNOUSERSITE=1`. The helper converts the selected
interpreter to an absolute path while preserving virtual-environment symlinks.
It performs no package installation or network access, and sets
`PYTHONDONTWRITEBYTECODE=1` and `PYTHONNOUSERSITE=1` for child commands.

Execution performs these checks in order:

1. Verify the original ZIP hash and all declared recovery files; preflight full
   extraction bytes and inodes before creating the destination.
2. Extract the full original packet and run its native `review.py verify`.
3. Call native `draw_main` with the original 32-byte seed to recreate frozen
   baselines. Recreate audits with their original seed. Compare every generated
   assignment contract byte-for-byte with its preserved original.
4. Initialize Git in the fresh **WORK** directory, confirm its exact root, and
   run `git apply --check` followed by `git apply` on the allowed patch.
5. Verify the final generator hash, restore declared public reports/evidence,
   and reconstruct source snapshots for preserved nonblocked solve episodes.
6. Run native offline runtime setup and the native `task_tests` gate. Its
   isolated prerequisite failure stops finalization. Then run every configured
   focused command using the chosen interpreter.
7. Recheck final source and retained report/contract hashes. Append the actual
   new test receipts to `RESULTS.json` without upgrading its completion state or
   rewriting its stopping reason, review prose, or solve history.
8. Run unchanged native `package_return.py` and confirm its final
   `patches/source.patch` hash equals the exact patch replayed.

## Solve records and private files

Packaging restored public records does not require private labels. The native
builder accepts `solve/source/generator.py` and
`solve-blind/source/generator.py`; this helper reconstructs those snapshots only
from exact hash-matching repository bytes. The post-repair episode must match
the final repaired source and final canonical ledger. The blind episode must
match its untouched assigned source and the original pre-patch canonical ledger.
Conflicting public or private source snapshots are rejected.

This restores the recorded episode; it does not create a new solve or replay
masked-query scoring. Finished attempts, exposure declarations and work logs stay
unchanged. Genuine blocked episodes remain blocked. A restored episode without
private labels cannot ordinarily be resumed with native `check` or `finish`;
continuing a solve is outside this helper's scope.

## Outputs, failures and limitations

| Exit | Meaning |
| --- | --- |
| 0 | Read-only plan is ready, or the unchanged native builder succeeded. Check `mode` and `official_return_created`. |
| 1 | Replay/check/package failed; the new workspace and receipts remain for review. |
| 2 | Invalid identity, hash, path, manifest or destination. No replay begins. |
| 3 | Insufficient capacity. |
| 4 | Capacity could not be assessed reliably. |

`RECOVERY-FINALIZATION.json` in the new packet root records commands, working
directories, interpreter, outputs, return codes, timeouts and failure state.
Successful test receipts are also retained under WORK/checks and referenced by
the native return. The helper never cleans earlier workspaces or resumes into an
existing destination. A prerequisite failure leaves a real failure receipt;
provide a suitable interpreter and choose a new destination for another attempt.

The builder's ordinary source, baseline, assignment, solve and size guards remain
unchanged. In particular, the official ZIP's 25 MiB expanded-size and 256-member
budget can still block packaging. Bundling can reduce the number of members but
cannot remove the expanded-size limit. A successful capacity estimate or
synthetic orchestration test is not evidence that a real packet was replayed or
that a maintainer accepted its findings.

Run all standalone tool tests from the tooling directory with:

```sh
ZIP_PREFLIGHT_TEST_TMPDIR=/absolute/private/scratch python3 -B -m unittest -v
```

`RECOVERY_VERIFICATION.json` records the actual final tool verification and its
explicit distinction between synthetic fixtures and the unreplayed real packet.
