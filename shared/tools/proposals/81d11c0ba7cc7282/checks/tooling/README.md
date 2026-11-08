# Handoff replay tooling

`replay_review_return.py` is a locally enhanced copy of the supplied passive
proposal at
`repo/shared/tools/proposals/b89fcb4b9114fa2f/checks/tooling/replay_review_return.py`.
The exact supplied file is preserved as `replay_review_return_original.py`:

- Original SHA-256: `6719b2b266e578cfc7846cfbae9127e2004b5d5956a42d48550d474ee9aba4ab`.
- Enhanced helper SHA-256: `612e4fdf9b25cd5133499dc6837a42c293bae12df04a3284ec9c193e810029e5`.

The helper validates ZIP and patch paths, extracts into a new directory, verifies
the isolated Git root, and runs `git apply --check` before applying the patch. It
installs no dependencies and does not remove an extraction tree. Racket and tests
are separate caller-controlled steps.

## Explicit case-distinct original ZIP option

The default remains the supplied strict portable policy, including rejection of
case-fold aliases. `--allow-case-distinct-zip-paths` enables case-distinct members
only in the **original** ZIP after an actual filesystem probe under the chosen
`destination.parent`. The probe uses a fresh private temporary directory,
exclusively creates two names differing only by case, verifies distinct files and
contents, and cleans up its own small probe directory. Case-insensitive behavior
or a probe error prevents extraction. No operating-system name or assumed `/tmp`
behavior substitutes for that probe.

Exact duplicate members, normalized file/directory aliases, and regular-file
ancestor collisions remain errors. The member and ancestor checks use the same
case-preserving key in the explicit mode. All existing member-count, expansion,
path-traversal, permission/type, symlink, encryption, compression, patch-format,
new-destination, and isolated-Git guards remain in place. The return ZIP always
uses the strict portable validator.

This option is needed for the issued packet's two separate regular members:

```text
WORK/repo/generators/4fd85612056f/workspace/reviewer-tools/second-pass-d91c405b/MANIFEST.json
WORK/repo/generators/4fd85612056f/workspace/reviewer-tools/second-pass-d91c405b/manifest.json
```

## Complete applied-file verification

`--expected-files-manifest PATH` accepts the review's
`checks/replay/change-manifest.json` format. Its `changes` list must contain each
exact patch path once, with the same boolean `new_file` flag and a 64-digit
`after_sha256`; an optional `bytes` field must be a nonnegative integer. Duplicate
JSON keys and duplicate, unsafe, or non-`repo/` paths are rejected. Missing paths,
extra paths, and case-only path substitutions fail before extraction.

After patch application, the helper checks every listed modified or new file,
including empty new files. It rejects symlinks and nonregular targets, hashes
actual file bytes, and checks the optional byte count. A correct selected-generator
hash cannot mask a mismatch elsewhere. The JSON receipt contains the manifest's
own hash under `expected_files_manifest` and per-file results plus checked/matched
counts under `expected_files`. The existing `--expected-generator-sha256` check
remains independently available.

For a complete replay, run from `WORK/`, substituting real input ZIP paths and a
new destination beneath an existing case-sensitive parent:

```bash
python3 -B checks/tooling/replay_review_return.py ORIGINAL.zip RETURN.zip /existing-parent/fresh \
  --allow-case-distinct-zip-paths \
  --expected-files-manifest checks/replay/change-manifest.json \
  --task-id 72f0b65569a4 \
  --expected-generator-sha256 437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f
```

## Bounded verification retained

The stdlib suite was written before the repair. Against the original helper it
ran 12 tests and failed with 15 failure entries, including subtests, because the
new opt-in and manifest APIs were absent. The strict-default and destination
symlink guards passed. After the repair, **12/12 tests passed with exit 0**, no
errors or skips, in 0.050 seconds. The suite covers exact duplicates, safe case
pairs, uppercase file/ancestor collisions in both orders, a simulated
case-insensitive destination, probe I/O failure, preserved path/return-ZIP guards,
and complete manifest set/hash checks including a newly added empty file.

Run the same suite from the outer extraction directory:

```bash
TMPDIR=/dev/shm python3 -B WORK/checks/tooling/test_replay_review_return.py
```

`tests-green.log` retains the actual successful output. `commands.json` records
the actual working directories, commands, exits, and source/test hashes.

The subsequent read-only original-ZIP preflight passed with exit 0 on all
**74,827 regular members**, zero directory entries, and **1,060,303,895 declared
expanded bytes**. The only case-fold alias group was the pair above. The actual
`/dev/shm` parent probe confirmed case-sensitive behavior. Full identity, counts,
and the explicit `extraction_performed: false` limit are in
`original-zip-validation.json`; its exact command is retained in `commands.json`.
This check validated archive metadata without extracting the packet, applying a
patch, or executing Racket. The original first replay failure remains separately
retained under `checks/replay/exact-patch-attempt1*.json`.
