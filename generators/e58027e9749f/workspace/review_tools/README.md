# ZIP-backed return packaging for a constrained workspace

`zip_readonly_overlay.py` supplies a restricted, read-only view of original
repository files that were never materialized. It passes a `PosixPath` subclass
to the **unmodified** official `arcpuzzles.review_full_return.build_full_return`.
The official builder still enforces patch scope, checks protected sources, builds
INTAKE/RESULTS and writes and validates its ordinary delta ZIP. The adapter calls
the same official validator again. It does not execute returned generators or
replace official replay and focused fresh-checkout tests.

## Integrity and failure policy

The source archive and cumulative historical extraction receipt are independent
trust anchors. Before enabling fallback, the helper checks their pinned SHA-256,
rejects unsafe/duplicate/nonregular archive members, requires exact inventory
agreement with the packet manifest plus outer entrypoints, and streams **every**
declared original member through SHA-256. The physical packet manifest and outer
entrypoints must be present and unchanged. Every original listed in the pinned
extraction receipt must still exist physically.

Existing physical files always take precedence, including modified files and
newly materialized originals. Missing previously materialized files fail rather
than falling back to the ZIP. Fallback applies only to never-materialized
`WORK/repo/` originals outside the selected task, canonical JSONL and the exact
assignment baseline paths. Unrelated original base-data files remain eligible.
Reports, checks, solves, private state and frozen baselines remain physical.
Unknown new physical repository files are enumerated so the official builder can
reject them. Symlinks and parent traversal are rejected. Writes address the real
filesystem; they never modify the original archive.

Before importing official Python code, the CLI authenticates physical `.py`
sources under `repo/src`. Its guarded import interval rejects preloaded
`arcpuzzles` modules, source symlinks, adjacent sourceless `.pyc` modules and native
extension candidates. It selects a fresh empty bytecode-cache namespace and
disables bytecode writes throughout official imports, build and validation, then
restores the previous Python settings and import path. This prevents old or
poisoned compiled caches from superseding the checked source. Archive and
receipt hashes are checked again after packaging.

The extraction receipt must cover the **complete historical union** of extracted
originals. Do not regenerate it after deletion: the current filesystem cannot
reconstruct that history. Extend and independently pin the cumulative receipt
before using the helper after further extraction. The command below uses the
review's cumulative v2 receipt, not the superseded first receipt.

## Packaging command

From `WORK/`, use the selected Python interpreter and a new output filename.
The source ZIP and cumulative receipt pins for this review are exact:

```bash
python3 -B repo/generators/e58027e9749f/workspace/review_tools/zip_readonly_overlay.py \
  --archive '/workspace/scratch/70785a599723/upload/SEND-THIS-ARCpuzzles-review(20261019-083126).zip' \
  --work /workspace/scratch/70785a599723/packet/WORK \
  --inventory /workspace/scratch/70785a599723/packet/EXTRACTION-v2.json \
  --source-sha256 3a511499c0c72de557e439c5ce40063af53c41ecfee70488aa93ed72f6baaadd \
  --inventory-sha256 31c4c524d2933b8425876483a614e9f8b07efd3aad8d02650d5e30a0ff350c20 \
  --task-id e58027e9749f \
  --out /absolute/new/review-response.zip
```

Use an execution environment permitted to access the physical WORK, source ZIP
and output. Add `--bundle-evidence` when requested; the unchanged builder also
bundles checks automatically when needed for its member limit. Do not package
until reports and solve records are ready. All integrity failures abort; there
is no fallback that suppresses a missing extracted file, changes source scope or
relaxes official validation. A successful package still needs the official
fresh replay and subsequent focused tests described below.

## Focused checks and limits

From `WORK/`, the standard-library helper tests can use the real official source:

```bash
ARCPUZZLES_TEST_SRC="$PWD/repo/src" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s repo/generators/e58027e9749f/workspace/review_tools \
  -p test_zip_readonly_overlay.py -v
```

Thirteen tests passed under unittest and pytest; retained commands, source hashes
and complete logs are in `WORK/checks/packaging-tool/`. They cover exact original
reads/enumeration, physical-file authority and deletion protection, pinned
inputs, manifest/member corruption, protected paths, writes/new-file discovery
and symlink/traversal rejection. The integration fixture calls the real official
builder: clean shared sources reach missing-report checking, while tampering is
rejected. Import fixtures demonstrate ordinary imports executing poisoned
unchecked-hash caches and direct sourceless bytecode, then verify the guarded
context ignores or rejects those alternatives. Preloaded modules, native module
candidates, source symlinks and restoration of Python settings are also checked.
These fixture results are separate from actual final packaging/replay evidence.

This is a POSIX adapter for this official builder API, not a general virtual
filesystem: only `rglob("*")` is implemented, and casting to an ordinary `Path`
drops fallback. The builder still holds payloads in memory and reads complete
individual files. The helper, Python interpreter and standard import machinery
are trusted infrastructure. The manifest is not an independent signature, and
the receipt's pin must come from trusted extraction history. Package only from a
quiescent workspace: concurrent writers can race reads, as with the original
builder. The after-build pin check detects changes to the archive/receipt but
does not make the whole live filesystem transactional. No shared source or
approval status is modified by this proposal.

# Review resource helper: a private temporary filesystem

`run_with_private_tmpfs.py` runs a command argument vector in a new Linux user and
mount namespace, with one bounded **512 MiB tmpfs** at a new empty owned directory
under `/tmp`. It sets only `TMPDIR` for the command. PATH, interpreter/venv,
working directory and the rest of the environment remain inherited. It passes
stdout/stderr through, uses no shell for the command, and returns the command's
status (signals use the usual 128 + signal number).

The wrapper creates no mount in the caller's namespace and changes no existing
mount or source file. The new tmpfs uses `nodev,nosuid,mode=700`. Its contents vanish
when the private namespace exits; the wrapper then removes the empty underlying
mountpoint. As with other process wrappers, commands should wait for their own
children rather than leaving detached background processes holding a namespace.

**Write reports, receipts, checkpoints and other retained outputs outside TMPDIR.**
For this review, `WORK/checks/` is outside the mount. For a portable invocation from
`WORK/`, substitute the selected Python path if the review uses an isolated venv:

```bash
python3 repo/generators/e58027e9749f/workspace/review_tools/run_with_private_tmpfs.py -- \
  python3 run_with_racket.py python3 -m arcpuzzles check e58027e9749f \
  --stage task_tests --phase after --out ../checks/task-tests-private
```

The Racket wrapper changes its payload cwd to `WORK/repo`, so the output argument
above names `WORK/checks/task-tests-private`. Inherit the already selected Racket
PATH and venv; this resource wrapper does not install or select them.

User namespaces and permission to mount tmpfs within them are required. The parent
review process successfully tested `unshare --user --map-root-user --mount --fork
true` in this environment. On a system blocking those facilities, the helper
fails with the actual diagnostic; it does not relax tests or change source-copy
rules. The tmpfs size is a quota, not guaranteed available RAM. Keep native stages
serial and monitor memory when running in a constrained environment.

The retained smoke test in `WORK/checks/private-tmpfs/` writes, reads and deletes a
small file inside the active mount and records filesystem type, exact mount
options, TMPDIR and status. It does not run a puzzle, assignment or Racket test.
The optional GUI-runtime deletion receipt in the same evidence directory records
only the separately authorized removal of installed `lib/gracket`; console Racket
and all collections/caches remain unchanged.

# Exact return replay followed by focused fresh-checkout tests

`replay_and_test.py` is a standard-library driver for the unchanged public
`arcpuzzles review replay-return` command and a separate subsequent pytest run.
Run it through `run_with_private_tmpfs.py` using the same prepared venv interpreter
that provides pytest, NumPy and Pillow. Inherit the already selected authentic
Racket executable through PATH/RACKET_PATH. It does not select or install dependencies.

From `WORK/`, use absolute paths for the two ZIPs and a **new persistent** output
directory. Substitute the selected venv interpreter for both `python3` occurrences:

```bash
python3 repo/generators/e58027e9749f/workspace/review_tools/run_with_private_tmpfs.py -- \
  python3 repo/generators/e58027e9749f/workspace/review_tools/replay_and_test.py \
  --source-zip /absolute/path/to/original-source.zip \
  --return-zip /absolute/path/to/final-review-response.zip \
  --compare-work /absolute/path/to/WORK \
  --out /absolute/path/to/WORK/checks/final-replay-and-tests \
  --test-timeout 600
```

The task ID comes from `ASSIGNMENT.json`. The output directory must not exist and
must be outside TMPDIR. The fresh replay checkout and both fresh Python cache
namespaces stay inside the private temporary filesystem. The driver calls the
official CLI from the comparison `WORK/repo` with only that repository's `src`
on PYTHONPATH, user site packages disabled and inherited ARCPUZZLES_HOME removed.
The normal official source authentication performed during final packaging is
still required; this driver does not substitute for it or modify the official CLI.

On successful replay, pytest runs from the fresh checkout's `WORK/repo` against
`generators/<task>/tests` and the fresh task-owned packaging helper test file.
It uses `--import-mode=importlib`, only the fresh `shared/runtime` and `src` on
PYTHONPATH, and ARCPUZZLES_TEST_SRC pointing to fresh `src`. Bytecode writing,
user site packages and automatic third-party pytest plugins are disabled;
inherited PYTEST_ADDOPTS/PYTEST_PLUGINS are removed. The prepared interpreter's
ordinary dependency site-packages and inherited Racket runtime remain available.
The timeout bounds the pytest subprocess; a timeout kills its process group.

Persistent output contains full `replay.stdout.log`/`replay.stderr.log`, exact
copies of official `replay.json` and `extraction-manifest.json.gz`, full fresh-test
logs, `fresh-tests.xml` and a separate `driver-receipt.json`. Available official
receipts are copied even if replay fails. The official receipt remains unchanged
with `patch_replay_passed_tests_pending` and `tests_run: false`; later test status
belongs only to the driver's separate receipt. That receipt records actual argv,
cwd, exit status, selected Python environment, test counts and the official patch,
changed-file and generator hashes. It independently rehashes the fresh generator
and changed files after tests and fails if they differ from replay's verified bytes.

The driver has been compile-checked. A real packaged return's subsequent replay
is the integration check; no candidate was replayed while authoring this helper.
The ephemeral checkout paths in copied official receipts stop being available
when the private wrapper exits. Retained hashes, logs, inventory, original ZIP
and exact return ZIP allow that checkout to be reconstructed when needed.
