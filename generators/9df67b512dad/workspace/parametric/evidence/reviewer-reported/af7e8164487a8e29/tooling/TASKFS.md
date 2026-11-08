# Task filesystem command bridge

`taskfs.py` sends a command to a UNIX-socket server already running in an approved private task session. It does not create namespaces or mounts. The server socket is created with mode `0600`.

## Approved execution context

Namespace creation and client execution require their explicit approved execution context. This helper grants no authorization to access host files, unrelated work, or other data. It is a **trusted-command bridge**, not a filesystem sandbox: `--cwd` must resolve beneath the server root, but command arguments and subprocess file access are not confined by the helper. Run only commands already authorized for the task.

The isolated task root lets work continue without deleting other work. Its tmpfs is **ephemeral**: checkpoint the assignment, changes, and evidence to the task's persistent deliverable before the session ends. A free-space snapshot is not evidence of a per-model quota or a host-wide byte limit.

## Commands

Start the server only inside an already approved private task session:

```sh
python -B /absolute/path/taskfs.py --socket /absolute/path/taskfs.sock serve --root /absolute/path/task-root
```

Run a client from the approved execution context:

```sh
python -B /workspace/scratch/27ff678e8110/taskfs.py --socket /workspace/scratch/27ff678e8110/taskfs.sock run --cwd WORK/repo -- python3 -B your_script.py
```

With `exec_command`, this session uses `sandbox_permissions="require_escalated"` and prefix rule `["python", "-B", "/workspace/scratch/27ff678e8110/taskfs.py"]`. Ordinary sandbox execution cannot connect to this session's socket; the helper is not a substitute for approval.

Place `--cwd` before the `--` separator. Its default is the server root; relative paths resolve beneath that root. The command is passed as an argv list, without a shell. Standard input is closed. Standard error is merged into the text output stream. Unicode text and a normal nonzero exit status were checked. This interface is for text output, not byte-exact binary transport. A rejected request returns exit status `125`.

The server sets `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR=<server-root>/tmp`. It refuses to replace an existing socket.

## Validation artifacts

- `taskfs-validation.json`: observed output, exit status, cwd containment, and own-root filesystem metadata from bounded independent checks.
- `taskfs.py`: exact copy of the validated helper, identified by SHA-256 in the receipt.

These checks cover the bridge only. They do not establish packet, native-runtime, puzzle, or prototype correctness.
