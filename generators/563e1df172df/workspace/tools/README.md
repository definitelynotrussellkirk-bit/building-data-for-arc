# Lossless compressed review evidence

`compressed_evidence.py` is a standard-library CLI for the supported
`arc-review-evidence-archive-v1` index. It preserves exact raw bytes, including
failures and embedded source/path references. It does not execute evidence.

Stop evidence writers first. From `WORK/`, compress selected `checks/` files:

```bash
python3 repo/generators/563e1df172df/workspace/tools/compressed_evidence.py compress --root /absolute/path/to/WORK --manifest checks/compressed-evidence.json --backup-root /absolute/scratch/path/outside-WORK/new-backup checks/lesson-census.json checks/schedule-census.json
```

The manifest and backup destination must be new. Compressed files appear under
`checks/compressed/`, preserving each original hierarchy: `checks/a/b.json`
becomes `checks/compressed/a/b.json.gz`. Gzip uses `mtime=0`. Each index entry
retains `original_path`, `compressed_path`, `original_bytes`, `compressed_bytes`,
`original_sha256`, and `compressed_sha256`.

The tool writes an exclusive raw backup outside WORK, writes compressed bytes,
verifies both representations and the published index, then removes originals.
Unsafe paths, runtime copies, symlinks, collisions and overwrites are rejected.
Do not run concurrent writers. An interrupted/rejected operation may leave
verified backups or compressed files; inspect those files instead of deleting
evidence to force a retry. Source deletion begins only after all representations
have passed verification.

Keep the backup outside WORK when packaging. Update `RESULTS.json` evidence
paths to the retained gzip files/index and cite the index in the review's
retained question/audit evidence. Existing reports can retain original path and
hash references because restoration recreates their exact original names/bytes.

For file count, `python3 package_return.py --bundle-evidence --out NEW_ZIP`
uses the supplied outer evidence bundle. When a returned ZIP has that bundle,
**first** verify and extract it into a new or empty directory with the public
command, from WORK:

```bash
PYTHONPATH=repo/src python3 -m arcpuzzles review evidence-extract /absolute/path/to/return.zip --out /absolute/path/to/new-extracted-evidence
```

Then restore the indexed gzip evidence into a different **new** directory:

```bash
python3 repo/generators/563e1df172df/workspace/tools/compressed_evidence.py restore --root /absolute/path/to/new-extracted-evidence --manifest checks/compressed-evidence.json --out /absolute/path/to/new-restored-evidence
```

Restoration verifies every compressed/original size and hash before creating the
output directory, then exclusively writes `OUT/checks/...`. It needs the index
and its gzip files; it does not need the raw backup. Restoring into a separate
scratch directory avoids adding large raw reports back into a return package.
Exit 0 indicates completion; rejected operations return 2 with a reason.
