# Explicit, lossless evidence archival

This task-local proposed utility uses only the Python standard library. Its
root is always the directory supplied with `--root`; it never infers a WORK
directory from its own location. It compresses **only explicitly listed files**.
It has not been used to compress this review's actual evidence during authoring.

## Commands

From the extraction directory, after all checks that require raw receipts have
finished, replace the example relative filename with the intended report:

```bash
WORK/.venv/bin/python WORK/repo/generators/12ace26107fd/workspace/evidence_archive.py --root WORK pack checks/large-report.json
WORK/.venv/bin/python WORK/repo/generators/12ace26107fd/workspace/evidence_archive.py --root WORK verify
WORK/.venv/bin/python WORK/repo/generators/12ace26107fd/workspace/evidence_archive.py --root WORK restore
```

Multiple explicit files can follow `pack`. No glob expansion, recursive
discovery, size threshold, JSON parsing, or success/failure filtering is
performed by the utility. A failed report, binary file, or log retains exactly
the same bytes after restoration. Shell expansion, if the caller chooses to
use it, occurs before the CLI receives its explicit file list.

An absolute tool location and absolute `--root` work from any cwd. File paths
supplied to `pack` remain relative to that root. Paths must use `/`, and cannot
be absolute or contain empty, `.` or `..` components, backslashes, or NULs.
Symlink roots, files, and path components are rejected.

Defaults, both relative to the explicit root:

- Manifest: `checks/ARCHIVE-MANIFEST.json`
- Compressed files: `checks/archived/<original-relative-path>.gz`

`--manifest` and `--archive-dir` can override these defaults; provide these
options before the action. Keep the same manifest location for subsequent
`pack`, `verify`, and `restore` operations. Repeated packs append new members.
Repacking an already archived path is safe when its original is absent or has
identical bytes; a recreated different original is refused.

## Mapping, verification, and conflict handling

The manifest uses the repository-recognized
`arc-review-evidence-archive-v1` schema. Each `entries` row stores
`original_path`, `original_bytes`, `original_sha256`, `compressed_path`,
`compressed_bytes`, and `compressed_sha256`. Paths are relative to `--root`.
This permits explicit retrieval and lets the existing retention reader verify
compressed dependencies without executing the supplied restore code.

Gzip uses level 9 and `mtime=0`; repeated identical inputs in the same Python/
zlib runtime produce identical compressed bytes. The complete batch is checked
for unsafe paths and existing conflicts before any raw file is removed. Every
new gzip is written and then read back, its compressed size/hash checked, and
its bounded decompressed bytes compared with the original size/hash. The
updated manifest is atomically replaced **before** matching raw originals are
removed. An error leaves raw bytes or already verified, manifest-bound gzip
bytes available; failed evidence is never discarded because of its content.

`verify` checks every compressed dependency and its decompressed size/hash.
`restore` verifies the entire archive and preflights all destinations before
writing missing originals. It preserves existing identical originals and
refuses to overwrite differing bytes. Compressed files and the manifest remain
after restoration. Manifest traversal, duplicate members, file/directory
collisions, symlinks, corrupted members, and overwrite conflicts are refused.
Existing compressed files are reused only when their bytes already match.

Use one writer at a time. The atomic manifest update and repeated byte checks
protect ordinary interrupted workflows; this utility does not claim a
transactional filesystem or protection against a concurrently hostile process
replacing directories. File contents are preserved; filesystem metadata such
as timestamps and permissions is outside the evidence contract.

## CPU-only fixture tests

From the extraction directory, the exact authored test command is:

```bash
/workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python review.py run /workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python -m pytest generators/12ace26107fd/tests/test_evidence_archive.py -q
```

After relocation, update the interpreter locations. The test source lives under
the selected task's `tests/` directory and resolves the workspace utility using
public `reviewer_support.find_root`/`load_selected_generator` helpers and copied
`RUNTIME_MANIFEST.json` source mappings. No tool-path environment variable is
required. The earlier checks-local fixture remains historical authoring evidence.
The tests operate only on temporary fixtures. They cover binary/failure-byte round trips, gzip timestamp
and determinism, appended manifests, idempotent restoration, corrupted bytes,
wrong size/hash metadata, traversal, symlink files/parents, compressed-file
conflicts, and all-destination restore conflict preflight. Recorded commands,
exit codes, and red/green logs are under `WORK/checks/evidence-archive-tool/`.
