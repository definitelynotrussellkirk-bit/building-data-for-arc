# Proposed memory-backed official return launcher

This support tool runs the original `build_full_return` and
`validate_full_return` functions without changing their code. It is useful
when an immutable source packet and a selective review workspace fit on disk
but a second complete checkout does not. It is a proposed adapter, not a
shared-tool installation, source approval, or training admission.

## Requirements and invocation

Use Linux with `/proc/self/fd`, `memfd_create`, and file-sealing support;
Python 3.12 or later; and pinned `pyfakefs==6.2.0`. Run in a fresh interpreter
with no preloaded `arcpuzzles` modules and no concurrent WORK edits.
Install the optional dependency into an isolated environment. The main shear
prototype needs no pyfakefs dependency.

The adapter retains a compressed source snapshot plus a complete in-memory
workspace, so it requires RAM proportional to the packet. It limits the
compressed and expanded source to 1 GiB each and the archive to 100,000
regular files; these are rejection bounds, not guaranteed affordable sizes.
It writes only a new output ZIP outside WORK. Redirect stdout/stderr outside
WORK during packaging, then copy a completed receipt into checks if desired.

From the outer packet folder, after completing the review:

```bash
python3 -B WORK/checks/tooling/memory_package/package_in_memory.py --source-zip SOURCE.zip --source-sha256 SOURCE_SHA256 --work WORK --materialized-inventory MATERIALIZED.json --inventory-sha256 INVENTORY_SHA256 --out NEW-RETURN.zip
```

`SOURCE_SHA256` and `INVENTORY_SHA256` must be caller-pinned lowercase SHA-256
values, not invented strings. The frozen materialized-path inventory has:

```json
{"schema":"arcpuzzles-materialized-original-paths-v1","paths":["WORK/PACKET-MANIFEST.json","WORK/repo/...original-file..."]}
```

Record every original WORK path that was physically extracted, before
allowing deletions or source edits, and keep the inventory pin separately.
Do not regenerate it after a missing-file failure. For this submission,
`materialized-originals.json` was frozen after selective extraction and
before final reports; no original-source deletions had occurred. Its exact
hash and scope appear in the packaging receipt. Authentic current assignment
and complete frozen baseline files must be present in the actual WORK.

## What is verified

The original ZIP is copied and hashed into an anonymous Linux memory file,
then sealed against writes, growth, shrinkage, and seal changes. All archive
verification, official-code imports, and original staging use these same
immutable bytes. Replacing or changing the original pathname cannot change
the imported code. Archive paths, duplicates, regular-file modes, canonical
manifest bytes, complete declared inventory, and every source hash are
checked before packaging. Named sealing-constant fallbacks use the verified
Linux UAPI values from `linux/fcntl.h` and `asm-generic/fcntl.h`; syscall
failure or ineffective sealing remains a hard failure.

All actual WORK files are snapshotted with their modes. Symlinks and
nonregular files are rejected. Every path in the frozen materialization
inventory must still exist. A never-extracted original may be restored from
the verified source; a missing previously materialized original is an error.

Before overlaying review files, the unchanged original `_base_paths`
function runs on the original-only staged workspace. The declared baseline
map must exactly equal that complete original source map; the frozen file
set and every frozen hash must match. This binds the supplied assignment's
baseline to original bytes. It does not independently authenticate the
history or randomness of the supplied assignment. Existing official checks
still validate its task, generator, question, and packet bindings.

The official builder runs on the full staged tree with actual review bytes
overlaid. Shared-source edits, unauthorized additions, disallowed task
changes, and unsafe executable modes remain visible to its checks. After
leaving pyfakefs, the original validator checks the return, WORK is resampled
to reject concurrent changes, and a new output is written without overwrite.
The exact saved ZIP is validated again in the real filesystem context.
Output containment uses normalized paths after rejecting symlink ancestors.

## Retained tests and remaining scope

`self-test.json` records byte-identical output from ordinary and memory
packaging of a tiny genuine official draw; the same partial workspace also
reconstructs identical output. It retains rejection of changed manifests,
shared files, source pins, source members, missing files, shortened or
invented baselines, executable source modes, unsafe paths, symlinks, and an
output path alias into WORK. It verifies immutable import bytes under source
path replacement/mutation and refusal to overwrite an existing output.

Reproduce the bounded tool tests with a fresh interpreter:

```bash
python3 -B WORK/checks/tooling/memory_package/package_in_memory.py --source-zip SOURCE.zip --source-sha256 SOURCE_SHA256 --self-test --self-test-root EXISTING-TEMP-DIRECTORY
```

The first local bootstrap run lacked named sealing constants; its traceback
is retained separately in `self-test-bootstrap-failure.txt`. The subsequent
run passed after the Linux UAPI compatibility fix. The tests did not execute
production generators or Racket and do not prove full runtime closure.

The real submission also uses the public `arcpuzzles review replay-return`
command with `--runtime-closure`: this performs a fresh declared dependency
extraction, real Git patch checks/application, and exact changed-byte
comparison. Its receipt explicitly says it does not execute tests and does
not extract the entire original packet. Follow the retained command and
receipt; keep this scope separate from the main real-Racket results.
