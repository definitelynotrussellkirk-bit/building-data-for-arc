# Private memory workspace helper

`private_memory_workspace.py` runs one explicitly supplied command in a new Linux
user namespace and a private mount namespace. It mounts real tmpfs at a **new**
owned child directory. Python file operations, locks, executable files, subprocesses,
and filesystem checks remain native. It does not emulate filesystem APIs or alter
packet manifests or source. It uses only Python's standard library plus Linux
`unshare`, `mount`, and `umount` (normally supplied by util-linux).

## Run

Choose an existing parent directory you own. Both leaf paths below must be new;
existing paths, including empty directories, are rejected. Use an absolute path
to any input file or script because the command starts inside the memory tree.

```sh
python3 -B private_memory_workspace.py \
  --work-dir /absolute/owned/parent/review-memory \
  --output-dir /absolute/durable/parent/review-result \
  --size-mib 768 \
  -- python3 /absolute/path/to/review_job.py
```

The command receives these environment variables:

| Variable | Meaning |
| --- | --- |
| `MEMORY_WORK_DIR` | Mounted working directory and initial command directory. |
| `MEMORY_RETURN_DIR` | Its `return/` subdirectory; put final files and desired failure evidence here. |
| `MEMORY_OUTPUT_DIR` | New destination outside the transient tree. Do not write into it directly. |

Before the namespace exits, the helper copies `return/` into `--output-dir` and
flushes ordinary exported files. It exports after both successful and failed
commands. The command's exit status is preserved when export and unmount succeed;
setup/export/unmount errors return nonzero (usually 70), and argument errors return 2.
The output destination still needs available bytes and inodes. A copy failure
returns 70; after namespace exit, unexported transient contents cannot be recovered.
A missing executable returns 127. The destination must remain empty until export;
the helper refuses to overwrite content or follow symlink/special-file exports.

For example, a job can finish by writing only its delta ZIP to
`Path(os.environ["MEMORY_RETURN_DIR"]) / "review-response.zip"`. Archive extraction
and review commands belong in that explicit job; this utility does neither.
An explicit shell command such as `-- sh /absolute/path/to/job.sh` is permitted.
The helper itself always launches argument lists with `shell=False`.

## Lifetime and limits

**The namespace must remain alive while the work runs. Files that were not exported
are transient and disappear when that namespace's last process exits.** This helper
keeps the foreground command alive, exports, unmounts its one private mount, and
exits; it starts no holder process. The command must finish all foreground work. Do not launch detached workers;
background holders can prevent a clean unmount and extend namespace lifetime. A crash, forced
termination, export failure, or loss of the containing environment can lose work.
Save important checkpoints explicitly to durable storage during long jobs.

An output outside this helper's mount is not necessarily durable: select a genuinely
durable filesystem. If the helper is itself run inside another temporary namespace,
its output still depends on that enclosing namespace. The smoke test here verifies
survival of the helper's child namespace; the parent review process must persist
these tool files and evidence before its own namespace exits.

The default limit is 256 MiB; this review used a 768 MiB workspace, as in the
example. `--size-mib` is an upper bound, not reserved memory. tmpfs uses system memory and may
use swap; excessive requested or actual usage can cause resource failures. The
helper supports Linux only and clearly fails when user namespaces or mounting are
unavailable. It never falls back to a host mount, scans unrelated directories, or
cleans another session's files. It leaves its newly created empty mountpoint and
output directory in place. It enumerates only its explicit `return/` export tree.

This is a storage workaround for trusted commands, **not a security sandbox**:
the command still sees and can access the rest of its permitted filesystem.
Run it from a parent directory you own and control; avoid concurrent renames of
that parent or its paths. No installed package, borrowed virtual environment,
network download, or administrator-level host mount is required.

## Focused verification

```sh
python3 -B test_private_memory_workspace.py
```

The tests use only their own temporary directories next to the helper. They cover
argument/path validation, real namespace creation, literal argv forwarding, output
survival, exit-status propagation, and symlink export rejection. Test directories
are removed by their owning test. `memory-workspace-smoke.json` records a separate
real 4 MiB invocation and links the retained `smoke-output/probe.json` result.
These helper checks do not establish generator or Racket correctness.
