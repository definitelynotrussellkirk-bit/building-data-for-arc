# Preserve a completed JSON receipt in gzip form

`compress_evidence.py` uses only the Python standard library. It compresses an
existing JSON report, verifies an exact-byte roundtrip, and leaves the original
file in place. It never reruns or rescores the report and makes no new semantic
or approval claim.

From the outer packet directory:

```bash
python3 review.py run python3 generators/48283e01e8ab/workspace/review_tools/compress_evidence.py ../checks/lesson-census.json
```

For `lesson-census.json`, the utility writes two adjacent files:

- `lesson-census.json.gz`: deterministic gzip with an empty embedded filename
  and `mtime=0`, containing the exact original bytes.
- `lesson-census.compression.json`: native `arcpuzzles-evidence-gzip-v1` manifest
  containing original/compressed byte counts and SHA-256 hashes. Its paths are
  relative to the manifest directory, and its compressed path is the original
  path plus `.gz`.

Success prints a JSON receipt with both output paths and hashes, the utility
hash, and verified source-preservation and roundtrip flags. The command exits 2
if either output already exists, the input is not a regular JSON file, a path
uses symlinks, or verification fails. Existing files are never overwritten.
On a detected write/verification error, it removes only output files created by
that call. The original is never opened for writing, moved, or deleted.

## Retaining the result in a return ZIP

Keep the gzip, its neighboring manifest, the original compact summary, and the
compression command receipt. Before manually relocating the raw JSON outside
`checks/`, verify the recorded hashes and update `RESULTS.json` evidence paths
and report references to the files that will actually be packaged. The original
census command remains unchanged in the command log; compression is a separate
operation. A native manifest does not make an absent raw JSON path satisfy the
packager's `evidence_paths` check.

The utility always leaves the raw JSON in place, so running it alone does not
reduce the expanded return budget. After verified compression and reference
updates, a reviewer may keep the raw copy outside the return while transporting
its exact bytes through the gzip and manifest. Do not discard the only copy of
a failed result. `package_return.py --bundle-evidence` addresses member count;
its archive is still charged at the full size of its contained files.

To restore, first copy the gzip and manifest to a new directory. Run the
manifest's `restore_argv` there, then check the restored file's byte count and
SHA-256 against `raw_size` and `raw_sha256`. Restore from a copy because
`python3 -m gzip -d` can overwrite an existing file at the decompressed path;
the new directory keeps retained evidence separate from restored working files.

Focused CLI contract probes are retained in
`checks/compression/test_compress_evidence.py`:

```bash
python3 review.py run python3 -m pytest -q ../checks/compression/test_compress_evidence.py
```

They exercise byte-preserving roundtrip, deterministic output across filenames,
native manifest hashes, collisions with each neighboring output, and rejection
of malformed JSON without creating outputs.
