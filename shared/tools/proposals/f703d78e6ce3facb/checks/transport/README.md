# Exact evidence compression and restoration

This standalone Python 3 standard-library tool preserves every byte of explicitly
selected evidence. It does not parse reports, filter failures, or choose files.
All examples below run from the packet's `WORK/` directory. The output directory
must be new, and its parent must already exist. No actual packet evidence was
compressed or removed during development; tests use synthetic temporary files.

## Compress without removing originals

```sh
python3 checks/tooling/evidence-compression/evidence_compression.py compress --root . --out checks/compressed-before checks/before/checks/d982cffd80f8_before_override_results.json
python3 checks/tooling/evidence-compression/evidence_compression.py verify --bundle checks/compressed-before
```

`compress` takes individual POSIX paths relative to `--root`; it accepts multiple
explicit files, but never globs or recursively discovers evidence. Shell wildcard
expansion is the caller's responsibility. The manifest records each original
relative path, raw byte size and SHA-256, compressed relative path, compressed
byte size and SHA-256. Gzip uses level 9, `mtime=0`, and an empty embedded filename.
The same raw bytes and relative names produce identical manifests and streams
with the same Python/zlib runtime. Different zlib versions may produce different
compressed bytes, while verified restored bytes remain exact.

To intentionally remove originals, append `--remove-originals` to a **new**
compression run with a fresh output directory. All sources are preflighted first;
the complete bundle is written and every compressed stream is verified against
both raw and compressed hashes/sizes before source removal starts. Source bytes
are checked again before removal. A compression or verification failure removes
the newly created incomplete bundle and leaves originals untouched. An error
during removal leaves the complete verified bundle in place, including copies
of any originals already removed. Never delete a bundle until restoration has
been verified and the retained-copy policy allows disposal.

## Restore into a new independent directory

```sh
python3 checks/tooling/evidence-compression/evidence_compression.py restore --bundle checks/compressed-before --out /absolute/path/to/a/new-restoration-directory
```

For example, that directory will contain
`checks/before/checks/d982cffd80f8_before_override_results.json` with its original
bytes. Restoration verifies the entire bundle before creating the destination,
checks each stream again while writing, and rolls back the newly created directory
on failure. Existing output directories/files are rejected, including empty ones.
Sources and destination ancestors must contain no symlinks. Manifest/source paths
must be relative and cannot contain `..`, `.`, empty components, backslashes, NULs,
duplicate entries, or file/directory collisions. Neither command overwrites an
unrelated file. Run without concurrent writers modifying the selected sources,
bundle, or destination; this small tool does not implement hostile concurrent
filesystem isolation or a power-loss recovery protocol.

`verify` also checks gzip integrity and bounds decompressed bytes by the manifest's
raw size. A successful CLI prints a compact JSON receipt and exits 0; data/path
validation errors print `error:` and exit 1; invalid CLI syntax exits 2.

## Return packaging

Keep the tool, README, manifest, compressed streams, and verification receipt in
`checks/`. The ordinary packager counts gzip files at their stored byte sizes,
so this reduces the 25 MiB expanded ZIP budget while keeping all original data
recoverable. If raw evidence is removed, update `RESULTS.json` command
`evidence_paths` to the **existing compressed stream and manifest**, and cite
the original path, raw SHA-256, and restoration instructions in the report.
The packager requires every listed evidence path to exist in the return.
The manifest is the original-path/size/SHA mapping required by RETURN-GUIDE.md.

## Tests and retained development receipts

```sh
python3 checks/tooling/evidence-compression/test_evidence_compression.py
```

The 11 CLI tests exercise deterministic multi-file/empty-file roundtrips,
explicit removal with recoverability, compressed corruption, false raw hashes
and sizes, traversal, duplicate/prefix collisions, missing targets, source and
destination symlinks, and output non-overwrite. Test directories are created only
under this tool directory and cleaned afterward. `red-test.log` records the
initial expected missing-tool failure; `collision-red-test.log` records the
explicit gzip-path collision regression before its preflight fix;
`green-test.log` records the final passing run. `TEST-RECEIPT.json` records exact
commands and status. These are development tests of synthetic data, not a claim
that packet evidence has already been compressed or restored.
