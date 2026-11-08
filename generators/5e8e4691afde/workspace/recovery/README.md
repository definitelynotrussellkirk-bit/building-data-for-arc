# Sparse ARC review return packaging

`sparse_package_return.py` packages an already assigned ARC review when a full
packet cannot be extracted. It uses only Python's standard library. It neither
draws assignments nor runs generators or reference rules.

This is a task-local recovery proposal. It does not modify or replace the
repository's shared packaging implementation. Keep the helper, tests, and this
README together in the reviewed task's `workspace/recovery/` directory.

## Package a review

Pass the **original full packet ZIP**, the extraction directory containing
`WORK/`, and a new output path outside `WORK/repo`:

```bash
python3 -B sparse_package_return.py \
  --archive '/path/to/SEND-THIS-ARCpuzzles-review(20261023-093525).zip' \
  --root /path/to/arc_review \
  --out /path/to/review-response.zip
```

The extraction directory must contain `MATERIALIZED.json` with this schema:

```json
{
  "schema": "arc-review-materialization-v1",
  "archive_sha256": "64 lowercase hexadecimal characters",
  "entries": [
    "START-HERE.md",
    "WORK/PACKET-MANIFEST.json",
    "WORK/repo/src/arcpuzzles/review_full_return.py"
  ]
}
```

The example entries are illustrative; retain the actual complete inventory
recorded while extracting the packet. Entries are original archive file names,
including the `WORK/` prefix. Every original file materialized on disk must be
listed, and every listed file must still exist as a regular file. Add an entry
whenever another original archive member is extracted. Never rebuild the
inventory from the current filesystem or remove entries to bypass an error:
that would erase the evidence needed to distinguish deletion from an original
file that was never extracted.

New authored files, including assignments, frozen baselines, review documents,
evidence, and new task workspace files, are discovered on disk and are not
original archive inventory entries. All source files named in the selected
assignment's `baseline_sha256` must have been extracted and inventoried. The
assignment's frozen `.review/baseline` files must also exist on disk.

`--inventory /path/to/MATERIALIZED.json` selects a nondefault inventory path.
`--bundle-evidence` forwards the original builder's evidence-bundling option.
The output ZIP must not already exist. Keep the input archive, inventory, and
working files unchanged while packaging runs.

## What is checked

The helper verifies the full archive's SHA-256 against the inventory, rejects
unsafe or duplicate archive paths and nonregular members, verifies the exact
archive/manifest file set, and hashes every manifest member directly from the
ZIP. It also checks the manifest's `layout.workspace` and exact
`layout.entry_files` mapping, including both outer entry file SHA-256 digests.
The manifest must retain the original canonical bytes. This helper targets the
supplied full packet layout with `START-HERE.md`, `review.py`, and `WORK/`.

Every present original file is read from its real working path. Only original
files that were never materialized can be read through the archive fallback;
assigned baseline sources cannot use that fallback. Missing inventoried files,
unrecorded materialization, symlinks, and special filesystem objects are errors.
The symlink check also covers ancestor directories and evidence directories.

The helper loads the **unchanged official Python modules from verified archive
bytes** into an isolated module namespace. It calls the original
`build_full_return`, including its source hash, frozen baseline, path scope,
canonical row, executable source, evidence, and completion checks. It then
calls the original `validate_full_return` explicitly again on the completed
ZIP. No official guard is monkeypatched or replaced. A changed shared Python
module on disk cannot execute before the official shared-source hash guard
rejects it.

The archive and extraction inventory are trusted inputs from the review
session; the inventory hash binds these inputs but is not an external digital
signature. The helper produces the same reviewer-reported return format as the
official builder and does not add an approval or training-admission claim.

## Regression tests

The tests construct a small synthetic packet using the official shared Python
modules from the supplied archive. They do not inspect or run an original
generator or reference rule. No original archive is fully extracted.
`ARC_SPARSE_SOURCE_ZIP` is required explicitly; the tests do not infer an archive
location from the task workspace.

```bash
ARC_SPARSE_SOURCE_ZIP='/path/to/original-packet.zip' \
  python3 -B -m unittest discover \
  -s /path/to/directory-containing-these-files \
  -p 'test_sparse_package_return.py' -v
```

Coverage includes a normal source delta, a new allowed workspace file, changed
shared code, deleted tracked files, file and ancestor symlinks, archive and
manifest hash mismatch, changed local manifest, an unallowed new source file,
corrupt frozen baseline, executable source, an unrelated canonical row edit,
unrecorded extraction, an undeclared archive member, path traversal, and an
unknown inventory member, plus the outer entry hashes and exact packet layout.
