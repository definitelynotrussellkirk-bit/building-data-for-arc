# Optional local packet tools

These standard-library Python tools are proposals for local review work. They do
not replace or modify any official ARCpuzzles controller, contract, manifest,
assignment draw, validator, or packaging gate. Run from a directory containing
all four sibling scripts. Paths are explicit. Python 3.11+ and Linux are the
intended environment for the private build/replay drivers.

## Tools

| File | Purpose | Main limit |
|---|---|---|
| `support_sparse_packet.py` | Stream-verify the original ZIP; plan/bootstrap/hydrate declared runtime closures; retain edited files; record omitted path/hash inventories in one gzip receipt. | A sparse workspace cannot satisfy official full-workspace verification or packaging. |
| `build_return_full.py` | Fully extract onto private tmpfs, run unchanged outer verification, overlay authored inputs, package officially; optionally replay/test. | Needs about 2 GiB of additional RAM and enough tmpfs inodes. |
| `build_return_overlay.py` | Borrow only an existing exact-manifest repository as an OverlayFS lower; hash every issued path, restore all differences from the original ZIP, hide extras, then verify/package officially. | Cache may disappear or change. Needs Linux namespaces/OverlayFS and memory for official subprocesses. |
| `replay_return_private.py` | Official fresh runtime-closure replay, fresh Python pytest environment, and portable selected-task tests through the fresh unchanged review wrapper. | Needs additional transient RAM, pytest installation access, and our own verified Racket installation. |

## Start with original integrity

```sh
python support_sparse_packet.py self-test
python support_sparse_packet.py verify --zip ORIGINAL.zip --receipt original-verified.json.gz
python support_sparse_packet.py plan --zip ORIGINAL.zip --bootstrap
```

Extraction requires both `--dest` (the directory above `WORK`) and a new
`--receipt` path. Repeat `--task`, `--contract`, or `--member` to hydrate exact
runtime/source needs. Existing regular edits are preserved. Unsafe ZIP paths,
symlinks, duplicate/extra/missing entries, and mismatched hashes are rejected.
Receipt paths remain outside the protected repository. Run `--help` for examples.

## Draw integrity and blind-solving order

Official `draw_main` verifies selected baseline sources before committing its
pending journal. A sparse initial checkout must save one random seed outside
`WORK`, identify the selection using the official selector, hydrate the exact
selection, and call official `draw_main` with that same saved seed. Do not retry
ordinary `review.py start` after a missing-source failure without preserving the
selection: a retry can draw again. These helpers never choose a seed or draw an
assignment. Follow the packet's blind-solving duties before opening sources.

## Private official packaging

Run the build drivers under:

```sh
unshare --user --map-root-user --mount --fork python build_return_overlay.py \
  --zip ORIGINAL.zip --source-sha256 ORIGINAL_ZIP_SHA256 \
  --source-work OUR_REVIEW/WORK --cache-root EXACT_MANIFEST_CACHE \
  --mountpoint EMPTY_PRIVATE_MOUNTPOINT --out-dir NEW_OUTPUT_DIRECTORY \
  --name review_response_ASSIGNMENT.zip --reserve-output-mib 12
```

The overlay driver reads only the cache's packet-manifest hash and declared
issued repository paths (hashes and directory entries). It never reads another
review's solves, private state, reports, or checks. Only the repository is a
read-only overlay lower. Missing/different issued bytes come from the SHA-bound
original ZIP, never from assumptions about the cache. All extra repository files
are hidden in our private upper. The unchanged outer `review.py verify` hashes
the complete original workspace before authored changes are installed. The
unchanged official package builder validates the return.

Namespace creation and mount propagation isolation must succeed before any
mount. Mountpoints must be empty and separate from inputs/outputs. No owner
cache files are modified or deleted. Explicitly use only a cache you are
authorized to inspect. Cache removal or mutation can make the build fail.

The overlay driver reserves an exclusive final output file with
`posix_fallocate` before expensive work. Reserved zeros are not a ZIP success.
Only a `passed` build receipt and its matching exact output SHA establish
completion. Caught failures remove only the driver's own matching reservation.
A killed process can leave an explicitly uncommitted reservation and a running
receipt; retain/report that failure, then use a new output directory for retry.
Receipts/logs/outputs are never overwritten. Final output must fit the reservation.

## Fresh replay and tests

Prepare `tests.json` with the recorded portable task-directory command:

```json
[["-m", "pytest", "generators/TASK_ID/tests", "-q"]]
```

```sh
unshare --user --map-root-user --mount --fork python replay_return_private.py \
  --source-zip ORIGINAL.zip --source-sha256 ORIGINAL_ZIP_SHA256 \
  --return-zip EXACT_OFFICIAL_RETURN.zip --compare-work OUR_REVIEW/WORK \
  --mountpoint EMPTY_PRIVATE_MOUNTPOINT --out-dir NEW_VALIDATION_DIRECTORY \
  --tests-json tests.json
```

The official replay applies the validated patch to a fresh declared runtime
closure, checks every changed file against our reviewed source, and records
patch/source hashes. This fresh replay is explicitly partial; original full
verification is recorded by the package build. Tests are separate evidence.
The fresh Python venv may inherit system numpy/Pillow and privately installs
pytest. No old code tree or old Python venv supplies the tested application code.

Only our own vendor/native toolchain may be reused. Every original native file
is streamed against our issued archive; unissued runtime-generated files are
hidden in the private native overlay. The unchanged setup wrapper can chmod its
private binary copy while leaving the underlying cache untouched. This avoids
copying the whole native runtime. The original vendor duplicate in the fresh
checkout is replaced by our issued read-only bind. Use `--replay-only` to record
only official patch/hash replay when explicitly desired; this does not claim any
tests passed.

Full verification, packaging, replay, dependency setup, tests, and cleanup fail
closed. Resource failures and failed inherited fixtures remain failures. These
tools do not shorten an official battery, relax validation, claim a sparse tree
is full, alter admission, or turn an unfinished check into a pass.

## Retained validation receipts

The replay driver can reuse our own preallocated receipt inode with
`--reserved-receipt OUR_RESERVED_FILE --embedded-exports`; it keeps those bytes
reserved throughout validation, then truncates only after completion. This mode
retains exact official `replay.json` text, compressed extraction inventory, and
test logs inside one JSON receipt. For each `embedded_exports` entry, UTF-8
content is the original text; base64 content is decoded with
`base64.b64decode(entry["content"])`. Check its stored SHA-256 before optionally
calling `gzip.decompress` for a `.gz` inventory. The official replay JSON also
records the inventory's raw SHA-256. A running/failed receipt never establishes
success. Use a new receipt/output directory for retries.

## Validation retained in this return

The sparse helper passed four focused tests and streamed the entire original
archive. The overlay driver completed unchanged official verification of
103,283 workspace files plus both outer files, then official packaging. The
private replay driver applied all eight changed files and passed 91 tests plus
21 subtests in a fresh Python environment. Exact receipts are under
`checks/packaging/`; the native toolchain was independently matched to all 1,998
files in the issued vendor archive.

The full-extraction driver is a proposed alternative. Its small private-mount
probe passed, but its complete build attempt was interrupted under resource
pressure before official verification. Do not treat that attempt as end-to-end
validation. Cache-based packaging and fresh replay supplied the successful
final evidence. The initial sparse-helper disk-full test and packaging failures
remain retained.
