# Packet capacity and memory packaging helpers

These task-local tools address the measured storage shortage in this review.
They are optional helpers. The official packet builder and return validator
remain authoritative; neither tool changes approval or training status.

## Read-only capacity preflight

`packet_space.py` uses only the Python standard library. It inspects the ZIP
member layout, counts files and distinct directories, estimates allocated
filesystem blocks, and compares bytes and inodes with the existing destination.
The default margin is 10 percent. It does not extract or delete anything.

From the outer review directory:

```bash
python -B WORK/repo/generators/a2d9d069c7d5/workspace/tools/packet_space.py \
  /path/original-request.zip . --verify --json
```

`--verify` additionally streams SHA-256 checks for every manifest-listed WORK
file and outer entry file. Capacity and byte verification are separate results:
exit status 1 can accompany successful archive-byte verification when extraction
will not fit.

| Exit status | Meaning |
|---|---|
| 0 | Estimated fresh extraction fits |
| 1 | Insufficient estimated bytes or available inodes |
| 2 | Invalid usage or filesystem I/O failure |
| 3 | Unsafe or unreadable ZIP layout |
| 4 | Manifest inventory or content verification failure |

The estimate covers a fresh extraction of the ZIP itself, including any nested
archive as a file. It does not expand nested Racket archives, test quotas,
reserve capacity, inspect destination conflicts, or establish runtime correctness.

## Complete source image in memory

`package_in_memory.py` is a storage adapter for the packet's unmodified
`build_full_return`. It requires **Python 3.12 and pyfakefs 5.9.3**, the versions
used in this review. A scoped installation needs no other dependencies:

```bash
python -B -m pip install --no-cache-dir --no-compile --no-deps \
  --target /tmp/arcpuzzles-pyfakefs pyfakefs==5.9.3
```

The adapter first verifies the original ZIP's canonical v2 WORK manifest,
complete inventory, outer entries, safe raw filenames and every member's bytes.
It reads the real working tree without following directory symlinks, retaining
file bytes, file types, executable bits and symlink targets. It then constructs
the complete original tree in memory and overlays the actual working files.
Unknown shared files and altered shared sources remain visible to the official
builder. The only excluded tree is the disposable `.review/racket-runtime`
installation, which is neither packet source nor return evidence.

### Extraction inventory and deletion protection

`WORK/extraction_inventory.json` must retain the actual extraction history. Its
schema is `arcpuzzles-partial-extraction-inventory-v1`, with these fields:

- `source_archive_sha256`: SHA-256 of the complete original ZIP.
- `packet_sha256`: SHA-256 of the original canonical manifest bytes.
- `members`: the original ZIP member names that were physically extracted,
  including `WORK/` where applicable and the outer entry files.

The inventory in this review was recorded from the exact executed extraction
scopes and then extended when supplementary task sources were extracted. The
adapter also requires the entire initially extracted `repo/src/` and
`repo/shared/runtime/` trees, the selected task baseline paths, the manifest,
and the outer entries to remain inventoried. Each listed member must still
exist. Newly extracted original members require an inventory update.

Missing inventoried members are errors. Only original members that were never
extracted may be restored from the verified ZIP. Do not remove inventory rows
to conceal deletions or rebuild the inventory from a tree that may already have
lost files. The immutable `.review/baseline` bytes are checked separately.

### Read-only verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/arcpuzzles-pyfakefs \
python -B WORK/repo/generators/a2d9d069c7d5/workspace/tools/package_in_memory.py \
  --packet /path/original-request.zip --work /path/review/WORK --verify-input
```

This validates the input and materializes all source bytes in memory, checking
their roundtrip bytes and modes. It creates no return ZIP and makes no claim
that the review is complete or that any task executes successfully.

### Package into a new output file

When the review documents, evidence and `RESULTS.json` are ready:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/arcpuzzles-pyfakefs \
python -B WORK/repo/generators/a2d9d069c7d5/workspace/tools/package_in_memory.py \
  --packet /path/original-request.zip --work /path/review/WORK \
  --out /path/review/review_response_new.zip
```

The output path must be new and its parent directory must already exist. The
builder and validators are imported from the verified original ZIP; edited
working helpers cannot replace their code. The official builder creates the
delta and `INTAKE.json` with its normal baseline, allowed-path, shared-source,
evidence and return checks intact. After filesystem substitution ends, the
official validator checks the ZIP again using real filesystem APIs. The adapter
checks that its inputs did not change during packaging, writes the new ZIP,
validates that saved ZIP and compares its exact bytes. A failed save is removed.
The original ZIP and the working artifacts are never rewritten by this command.

### Focused tests

From `WORK/`, with the actual original ZIP substituted below:

```bash
python -B repo/generators/a2d9d069c7d5/tests/test_packet_space.py -v
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/arcpuzzles-pyfakefs:/path/original-request.zip/WORK/repo/src \
python -B repo/generators/a2d9d069c7d5/tests/test_package_in_memory.py -v
```

The memory-adapter tests use a small, explicitly synthetic review and the
unmodified official builder. They cover binary and text roundtrips, independent
return validation, shared-source corruption, missing extracted files, unexpected
shared files, executable and symlink source, changed immutable entries/baselines,
corrupt unextracted originals, raw NUL filenames and overlapping manifest maps.
`checks/tooling/memory_packaging_verification.json` records this review's actual
commands, exit statuses and source hashes.

## Scope and fresh replay

The memory adapter supports this v2 WORK-layout packet format with regular,
nonexecutable original members. It needs enough RAM for the full expanded
archive, working overlay and Python overhead, and enough real storage for the
compact return. It does not make native subprocesses operate on an in-memory
filesystem and does not replace a fresh public replay.

The prescribed public replay is a separate command after a return exists:

```bash
PYTHONPATH=/path/review/WORK/repo/src python -B -m arcpuzzles review replay-return \
  --source-zip /path/original-request.zip --return-zip /path/review_response.zip \
  --compare-work /path/review/WORK --out /path/new-replay --runtime-closure
```

It uses a new physical checkout, validates the source and return inventories,
applies the complete patch with Git, and compares every changed file's hash.
For this packet the unpatched declared closure has 347 files and 81 directories,
60,686,578 content bytes and an estimated 61,775,872 allocated bytes; patched
files, Git metadata and receipts need additional space. Its receipt explicitly
reports partial extraction and `patch_replay_passed_tests_pending`. It executes
no task programs or tests. Runtime/task checks and their limits must be reported
separately from archive verification and patch replay.
