# Lossless archived evidence

These archives retain superseded and intermediate evidence, including the failed
`checks/after/` battery and the privacy regressions. Compression does not change
any recorded outcome or remove failure evidence.

| Original location | Archive |
| --- | --- |
| `checks/after/` | `after-failed-seed-cap.tar.gz` |
| `checks/schedule-census-final.json` | `schedule-census-intermediate.tar.gz` |
| `checks/parametric/height-suite-v1/` | `parametric-height-suite-v1.tar.gz` |
| `checks/parametric/v2-privacy-red-fixtures/` | `parametric-v2-privacy-red-fixtures.tar.gz` |
| `checks/parametric/v2-focused-green-fixtures/` | `parametric-v2-focused-green-fixtures.tar.gz` |

`MANIFEST.json` maps every original file path to its archive, original byte
count, and SHA-256. It also binds compressed archive bytes and the decompressed
tar stream. `archives.json` supplies the repository's native
`arcpuzzles-evidence-gzip-v1` index for the tar/gzip byte streams. Keep this whole
`checks/compressed/` folder together when retaining or transferring evidence.

## Verify without restoring

From `WORK/`:

```bash
python3 checks/compressed/restore_evidence.py verify
```

This checks every compressed archive, every decompressed tar stream, and all
declared original member sizes and hashes. It rejects undeclared or duplicate
members, unsafe paths, and archive symlinks or other nonregular members.

## Restore to a new location

```bash
python3 checks/compressed/restore_evidence.py restore \
  --destination /path/to/new-restoration-directory
```

Restoration creates `checks/...` beneath that destination. All original regular
file bytes are exact. The tool refuses existing destination files and symlink
ancestors and never calls `tar.extractall`. It copies only declared regular
members and rehashes every restored file.

The four pytest `*current` symlinks are convenience aliases, not evidence files.
Their exact original absolute target strings, byte counts, and hashes are kept
in `MANIFEST.json`; portable restoration creates equivalent relative aliases
to the retained target directories. It never recreates an absolute link outside
the chosen restoration directory. File permission bits and timestamps are not
part of the byte-equivalence claim.

The `compression-receipt.json` records the actual packaging command, cwd, source
hashes, before/after sizes, archive validation, a full portable restoration
check, and unchanged hashes for protected final evidence. Originals were removed
only after archive verification, full restoration verification, and a second
check of their unchanged contents and directory inventories.

Final `after-final/`, `parametric/height-suite-v2/`, `schedule-census-v3.json`,
`lesson-census-v3.json.gz`, and small top-level failure logs remain in place.
To inspect a superseded path cited in an earlier report, restore these archives;
do not reinterpret the historical report as describing the final implementation.

## If an execution tool restores removed temporary files

During this review, old loose files and pytest convenience aliases reappeared across tool boundaries. Their archive bytes were intact. Two package attempts correctly refused the aliases. A separate completed cleanup invocation followed by the normal package command succeeded. The cause of the filesystem behavior is not established here.

The reviewer-side helper in `checks/package_verified_return.py` separates these operations. It refuses to remove any present file that differs from its archived hash or any undeclared path. Run cleanup as one completed command, then package as a later command:

```sh
python3 checks/package_verified_return.py --cleanup-verified-duplicates
python3 checks/package_verified_return.py --out review_response.zip
```

This helper is for the original WORK checkout after applying the assigned changes. It validates the finished solve/source binding and delegates the actual ZIP creation and limits to the supplied `package_return.py`.
