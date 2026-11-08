# Archive-backed packet validation

`archive_overlay.py` supplies read access to **explicitly recorded, absent,
immutable repository files** in a sparse extraction. It exists because the
original `arcpuzzles.review_full_return.build_full_return` checks every manifest
repository file, while this environment could not hold the full extraction.

This is archive-backed validation of omitted sources. It is **not a full
extracted-runtime replay**, a replacement validator, or an import hook. The
original builder, assignment and ticket checks, baseline validation, edit
detection, patch generation, and return validator remain unmodified.

## Usage

The runnable `package_sparse.py` imports the supplied builder from
`WORK/repo/src`, checks that its source has the original manifest hash, and calls
its original `build_full_return` function. A compact JSON result is printed to
stdout. The optional receipt includes the full verified virtual-path list; it
is written after the build and is not added to that return ZIP. Receipt files
must be new and outside `WORK/repo`.

```sh
python -B package_sparse.py \
  --work /absolute/path/to/WORK \
  --source-zip /absolute/path/to/original-packet.zip \
  --zip-sha256 61730ae7789a4e6d5fe21a4fc2e55648ef00a6a46b8e045c104ab4b0936cae5a \
  --omissions /absolute/path/to/WORK/checks/environment/sparse-omissions.json \
  --out /absolute/path/to/new-return.zip \
  --receipt /absolute/path/to/new-overlay-receipt.json
```

The omission list must have been recorded when the sparse extraction was
planned, **before review edits**. Do not construct it by listing whatever files
are missing at packaging time. Obtain the expected ZIP hash from the previously
recorded original-archive verification, not from an untrusted replacement ZIP.
For this supplied archive the recorded SHA-256 is:

```
61730ae7789a4e6d5fe21a4fc2e55648ef00a6a46b8e045c104ab4b0936cae5a
```

```python
import json
from pathlib import Path
from archive_overlay import ArchiveOverlay
from arcpuzzles.review_full_return import build_full_return

work = Path("/absolute/path/to/WORK")
original_zip = Path("/absolute/path/to/original-packet.zip")
environment = work / "checks/environment"
record = json.loads((environment / "archive-verification.json").read_text())
omitted = json.loads((environment / "sparse-omissions.json").read_text())

with ArchiveOverlay(
    work,
    original_zip,
    expected_zip_sha256=record["archive_sha256"],
    omitted_paths=omitted,
) as overlay:
    result = build_full_return(work, Path("/absolute/path/to/new-return.zip"))

report = overlay.report()
```

Each context object is single-use. A separate context requires a new object.
The default report records virtual read counts and SHA-256 digests of compact
JSON arrays of sorted path strings. `report(include_paths=True)` additionally
includes the complete list of verified virtual paths. Preserve the original
omission record separately. The report becomes available after successful entry.

## Boundaries

- The helper hashes the complete original ZIP before installing any dispatch,
  retains the same open file descriptor, and checks for archive mutation around
  reads. ZIP CRC checks and the packet manifest SHA-256 independently check every
  virtual file read.
- ZIP member duplicates, path traversal, ambiguous paths, file/directory
  conflicts, symlinks, other nonregular member types, and encrypted members are
  rejected. The local packet manifest must match the archive bytes exactly.
- Only allowlisted `repo/` manifest files can be virtual. Every selected-task
  path and every assignment baseline path is excluded. Frozen baselines,
  assignments, review documents, evidence, and output archives remain physical.
- Any physical object takes precedence. Existing corruption, directories,
  special files, symlinks, broken symlinks, unsafe ancestors, and permissions
  errors do not receive archive fallback. A path materialized at entry is never
  virtualized later, even if it is then deleted.
- The context dispatches only `Path.open`, `Path.exists`, and `Path.is_file`.
  `Path.read_bytes` and `read_text` use the dispatched read-only `open` naturally.
  Read-only streams reject writes. `stat`, `glob`, `rglob`, `builtins.open`, and
  import machinery still see the actual filesystem; virtual directories are
  not synthesized. This narrow interface matches the immutable-source check
  in the original builder.
- Write modes always call the original `Path.open`, so output creation and
  write failures are real. Attempting a write through `Path.open` permanently
  retires that path from virtual fallback. Observing a newly materialized
  object also retires it.
- Do not mutate omitted source paths concurrently with validation. A create
  and delete cycle performed entirely through `os`/`builtins` between overlay
  observations cannot be tracked. This is a read-only packaging context, not
  a general filesystem change monitor. The original builder only reads sources
  and writes its real output archive.
- Only the entering thread sees virtual reads. Nested/overlapping contexts
  fail. The three original `Path` methods are restored on success or exception.
  Do not independently monkeypatch `Path` methods during this context.

## Verification

Run from `WORK/repo/` without writing Python cache files:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B generators/c4f6a0585dbf/tests/test_archive_overlay.py
```

The tests use small synthetic packets and inspect no puzzle generator or hidden
rule. They cover omitted reads, physical corruption and deletion, symlinks,
directories and FIFOs, unsafe ancestors, real writes, archive hash/CRC/member
rejection, selection and baseline exclusions, restoration, single-use and nested
contexts, and thread isolation. An additional smoke check used the issued ZIP,
the real sparse root, all 7,462 recorded omissions, and one non-puzzle guide
read. Complete package validation and official runtime replay remain separate
steps using the original supplied tools.
