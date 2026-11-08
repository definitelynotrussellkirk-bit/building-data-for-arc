# Private tmpfs packet workspace proposal

`packet_tmpfs.py` is a standalone Linux recovery helper for extraction failures caused by exhausted disk bytes or inodes. It creates a new private user/mount namespace and mounts its own tmpfs over an existing, empty, task-owned directory. It does not rely on shared `/dev/shm` free space.

The helper runs the original packet unchanged. It does not draw an assignment, inspect puzzle solutions, modify repository files, skip verification, or build the official return itself. It needs Python 3.10+, Linux user/mount namespace support, and the `unshare` and `mount` utilities. If those capabilities are unavailable or denied, it fails; it does not escalate privileges automatically.

## Use

Create a new empty mount directory and an output directory outside it. Leave any earlier failed extraction intact. Use actual paths in place of these examples:

```bash
python3 packet_tmpfs.py /path/review.zip \
  --mountpoint /path/empty-mount --output-dir /path/saved-returns --dry-run

python3 packet_tmpfs.py /path/review.zip \
  --mountpoint /path/empty-mount --output-dir /path/saved-returns --shell
```

`--dry-run` (also `--preflight`) reports source SHA-256, regular files, explicit and implied directories, required inodes, expanded bytes, rounded allocation estimate, proposed tmpfs limits, output free space, and utility paths. It does not mount or extract. The default ceilings are at least 512 MiB and 32,768 inodes; larger packets receive twice their estimated allocation plus 256 MiB, and twice their entry count plus 4,096 inodes. These are ceilings and estimates, not memory reservations or guarantees of sufficient space for arbitrary future work.

**Keep the complete review in that one interactive shell.** Start with the packet's own `python3 review.py verify` and `python3 review.py start`, then follow its directions, including any blind solve before opening generators or rules. Run the original tests and packaging command. When the original packager has created `WORK/review_response_*.zip`, exit the shell to export it. Each new helper invocation starts from the supplied ZIP again; separate invocations do not resume an assignment or retain unsaved work.

A single command or complete noninteractive driver is also supported:

```bash
python3 packet_tmpfs.py /path/review.zip \
  --mountpoint /path/empty-mount --output-dir /path/saved-returns \
  -- python3 complete_review_driver.py
```

No shell is opened unless `--shell` is explicit. Command arguments are passed directly, without shell interpolation. `TMPDIR`, `TMP`, and `TEMP` point to a new directory at the private workspace root, outside `WORK/repo`, so dependency installers and subprocesses do not spill their temporary files back into an exhausted `/tmp`.

## Boundaries and export behavior

- The mountpoint must be an existing empty directory. Symlinks in its path, an already mounted directory detectable by `ismount`, and packet/helper/output paths inside it are rejected.
- ZIP paths are checked before any mount or extraction: absolute paths, traversal, backslashes, drive prefixes, duplicate names, file/parent conflicts, symlinks, special files, and encrypted entries are rejected. The child verifies the source SHA-256 again and uses the same opened archive for validation and extraction.
- Extraction uses exclusive file creation inside the new tmpfs and gives files nonexecutable permissions. The original setup script remains responsible for installing and enabling its bundled Racket runtime.
- Export considers only new regular ZIP files named `review_response_*.zip` directly in the packet root or `WORK`. Matching files supplied in the input ZIP and unrelated ZIPs are excluded. It does not export the checkout, original input, or arbitrary files.
- Existing output files are never overwritten. Duplicate output basenames, matching symlinks, invalid ZIPs, insufficient output bytes/inodes, and checksum mismatches fail explicitly. Successful copies are flushed, synchronized, and SHA-256 verified before success is reported. An interrupted copy can leave a partial newly created output file; the helper never deletes it.
- Ctrl-C reaches the command while the supervisors remain alive to export an already written response; an interrupted command returns status 130. Forced termination is still unsafe for unsaved data.
- A command that exits nonzero still gets an export attempt. Its exit status is preserved if export succeeds. A successful command without responses reports `no_response_zips_generated` and exports nothing.
- In explicit interactive shell mode, an export error reopens the same mounted workspace so the user can resolve the problem and exit to retry. This is a single supervised shell, not a persistent daemon. Export failure in command mode returns an error and the private workspace then disappears.

The original empty mountpoint and supplied ZIP remain intact after normal teardown. **Exiting without a response, forced termination, OOM, machine loss, or a noninteractive export failure can lose work held only in tmpfs.** Choose an output directory with enough bytes and inodes before starting. Keep the shell open until the original packager has produced the intended return. This helper does not validate the semantic completeness of an official review return; the original packager owns that check.

## Verification included

Run from this directory:

```bash
python3 -m unittest discover -v
python3 integration_fixture.py
python3 integration_signal_fixture.py
```

The 12 unit tests cover preflight counts, unsafe paths/types, duplicate and parent conflicts, empty-directory and symlink guards, missing tools, explicit command selection, response filtering, no overwrite, and empty exports.

The integration test uses a tiny synthetic ZIP and three actual private namespaces. It verifies exact exported fixture bytes, private temporary directories, unchanged input bytes, teardown isolation, no-output reporting, and preservation of a command exit status of 7 after export. A fourth integration case sends a real SIGINT to the synthetic process group and verifies that an already written response is exported before status 130 is returned. These fixtures are explicitly not official ARCpuzzles returns.

Raw stdout/stderr logs and exact command records are included. `07-original-packet-preflight.stdout.log` is metadata-only evidence for the supplied archive: 7,829 files, 4,225 directories, 12,054 required inodes, 190,580,413 payload bytes, and a proposed 688,914,432-byte / 32,768-inode tmpfs. The original packet was not executed through this proposed helper during these tests. Official review/package validation is separate.
