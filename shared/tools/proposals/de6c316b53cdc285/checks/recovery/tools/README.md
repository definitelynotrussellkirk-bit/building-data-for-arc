# Review archive and replay recovery tools

## Standalone review ZIP verifier

Run from any directory with Python 3 (stdlib only):

```bash
python /path/to/verify_review_archive.py /path/to/review.zip
python /path/to/verify_review_archive.py /path/to/review.zip --out /path/to/new-receipt.json
python -m unittest discover -s /path/to/recovery_tools -v
```

Without `--out`, the compact JSON receipt goes to stdout and no file is
created by the verifier. `--out` uses exclusive creation: an existing path is
an error, so reruns need a new receipt path. Exit status is 0 for a verified
archive, 1 for invalid/inconsistent archive content, and 2 for CLI or receipt
output errors. The archive is always opened read-only.

The supported manifest is `arcpuzzles-full-packet-v2` at
`WORK/PACKET-MANIFEST.json`, encoded as UTF-8 using
`json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))`
without a trailing newline. Workspace inventory paths are relative to
`WORK/`; outer entry inventory must name `START-HERE.md` and `review.py`.
The manifest itself is separately hashed, not part of its own file inventory.

Every payload is streamed in 1 MiB chunks, with ZIP CRC validation and an
independent SHA-256 check against the relevant manifest inventory. Receipt
hashes identify the complete compressed archive and exact manifest bytes.
The verifier rejects duplicate ZIP paths, duplicate JSON keys, path traversal,
absolute or noncanonical member paths, control characters, backslashes,
colon-containing names, symlinks and other special members, inventory
overlaps, unexpected files, missing files, and noncanonical manifest JSON.
Directory records are accepted only for expected parent directories.
Packet code is never imported or executed, and payload text is not parsed.

## Limits

- Hash consistency is not an authenticity signature. An attacker able to
  replace the archive and its manifest can create a self-consistent archive.
  Compare the archive SHA-256 with a separately trusted value when needed.
- Manifest metadata outside the file inventory/layout/schema is not
  semantically validated. In particular, `canonical_sha256` is not treated
  as a signature or reinterpreted as a manifest self-hash.
- Payload memory is bounded by the stream chunk. The ZIP central directory,
  per-file digest inventory, and manifest JSON remain in memory. The manifest
  is limited to 64 MiB; there is no archive-wide expansion/time limit.
- Actual byte counts are exact on success. On a corrupt member, bytes from
  fully streamed files are reported; partial bytes from that failed member
  are excluded, and the receipt is unsuccessful.
- Concurrent modification is detected by comparing the opened archive's
  device, inode, size, mtime and ctime before and after verification. This is
  a practical consistency check, not a filesystem snapshot guarantee.
- Checks cover the ZIP entries exposed by Python's `zipfile` reader; the tool
  is not a forensic parser for orphan local headers or trailing polyglot data.

`test_verify_review_archive.py` uses only tiny synthetic ZIP fixtures. It
does not select assignments or read puzzle-specific material.

## Archive-backed packaging under limited disk space

`package_verified_sparse.py` supplies never-materialized immutable repository
files from the original verified ZIP to the unchanged official return builder
and validator. It requires the materialization inventory and hashes every fallback
member. Physical files win; selected-task files, baseline, contracts, reports,
and protected paths cannot fall back. Its receipt explicitly identifies this
integration shim. It does not alter the official builder, rewrite assignment
identity, or manufacture an intake manifest or patch. The 13 synthetic packaging
tests and 12 verifier tests passed; their combined log is
`checks/recovery/tools-verification.log` relative to WORK.

```bash
python3 checks/recovery/tools/package_verified_sparse.py \
  --work . --archive /absolute/path/original.zip \
  --inventory checks/recovery/materialized-sources.json \
  --out /absolute/path/new_return.zip \
  --receipt /absolute/path/new_package_receipt.json --bundle-evidence
```

## Narrow manual fresh-copy replay

`manual_replay_selected.py` authenticates the original archive against the retained
full-verification receipt, invokes the unchanged official return validator, and
extracts the selected task plus the small source closure required by its direct
tests. It uses a new destination only, verifies the exact WORK Git root, applies
the returned patch with Git, and compares every changed/new file to reviewed
bytes. `--plan` performs authentication and previews the inventory without writes.
The utility itself never executes returned code or tests. Three synthetic tests
cover clean replay, mismatch rejection, and unsafe archive rejection.

```bash
python3 -B checks/recovery/tools/manual_replay_selected.py \
  --source-zip /absolute/path/original.zip \
  --return-zip /absolute/path/return.zip --compare-work /absolute/path/WORK \
  --source-verification checks/recovery/tools/original-archive-verification.json \
  --out /absolute/path/NEW_REPLAY
```

For this return, `checks/final-replay/replay.json` records 210 extracted original
files and the exact applied patch. `run_manual_replay_tests.py` is the companion
runner for the independent `NEW_REPLAY/venv` environment. It records dependency
versions, Racket executable hash, imported project-source paths, and all 14
changed-file hashes before/after pytest. Use a trusted Racket executable and a
fresh venv with pytest installed; this helper does not install dependencies.

```bash
/absolute/path/NEW_REPLAY/venv/bin/python -B \
  checks/recovery/tools/run_manual_replay_tests.py \
  --replay /absolute/path/NEW_REPLAY --racket /absolute/path/racket \
  --out /absolute/path/new_focused_test_receipt.json
```

The retained fresh run passes 65 tests and three subtests. These tools deliberately
do not satisfy the official runtime-closure replay or official task_tests stage.
The latter remains infrastructure-blocked in this review. Synthetic tests do not
prove portability to arbitrary packets; the source-subset selector is scoped to
this packet family and selected-task test dependencies.
