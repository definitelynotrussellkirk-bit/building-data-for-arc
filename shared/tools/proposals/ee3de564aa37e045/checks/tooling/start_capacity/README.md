# ARC startup capacity companion

`start_capacity.py` is a proposed standalone helper for an **already extracted**
ARC review workspace. It closes the observation gap between extraction capacity
and the additional space required by the official startup transaction.

It has three commands:

- `report`: read control metadata and filesystem statistics, then emit an
  aggregate startup capacity estimate as JSON.
- `checkpoint-pending`: copy an interrupted draw's exact control metadata into
  a new directory outside `WORK`.
- `verify-checkpoint`: check those saved bytes, hashes, and metadata bindings.

The helper never invokes the review engine, draws a task, changes a seed, writes
inside the supplied `WORK`, restores records, or marks review duties complete.
It does not open generator, rule, canonical-data, solution, note, or audit
contents. File-content reads are limited to the packet manifest, pending journal,
assignment record, and this helper's own checkpoint metadata. Printed results
omit seeds, task identifiers, baseline filenames, and task descriptions.

## Requirements and status

Python 3.10 or later; standard library only. No installation is required.

Reporting uses `statvfs` where available and falls back to `shutil.disk_usage`.
Filesystem type, inode counts, and visible cgroup-v2/host memory are reported
separately. Metrics unavailable on a platform remain explicit unknowns. Unknown
inode, filesystem-type, memory, or visible cgroup measurements prevent a
`ready` result. Unreadable or unresolved process cgroup membership also leaves
the measurement incomplete. Linux cgroup v1 is not implemented.

Pending checkpoints require POSIX `fcntl.flock` and the existing official
`.review/main-draw.lock`. The helper acquires a shared nonblocking lock, using
the same primitive as the official startup's exclusive lock. It never creates
or truncates the lock file. An active official draw causes a clean failure.
The tests qualify Linux/POSIX behavior only; Windows checkpoint behavior is not
supported or claimed.

This tool is advisory. It is not wired into `review.py start` or any intake gate.

## Report an existing workspace

From the directory containing this helper:

```sh
python3 start_capacity.py report --work /path/to/packet/WORK
```

To save the JSON, redirect stdout to a report location you control:

```sh
python3 start_capacity.py report --work /path/to/packet/WORK \
  > /path/to/reports/start-capacity.json
```

Default reserves are **512 MiB and 128 inodes**, beyond the modeled allocation.
They may be adjusted explicitly:

```sh
python3 start_capacity.py report --work /path/to/packet/WORK \
  --reserve-mib 1024 --reserve-inodes 512
```

Exit 0 means `ready` for the declared estimate. Exit 2 means `blocked`,
`indeterminate`, or `error`; inspect the JSON's failure and warning codes.
`ready` is a point-in-time estimate, not a guarantee that startup will succeed.

### Draw states

| State | Meaning for the next official startup |
|---|---|
| `unstarted` | Neither a pending journal nor assignment exists. No selection is made by this helper. |
| `pending_only` | The exact draw is journaled, but `ASSIGNMENT.json` has not been published. |
| `pending_finalization` | The journal and matching assignment coexist. Official startup may have been interrupted while finalizing outputs. |
| `completed` | An assignment exists and the startup journal is absent. The official startup's idempotent branch does not copy a new baseline. |

Conflicting pending/assignment records, unsafe paths, symlinks, unsupported
metadata, and an unjournaled partial baseline fail explicitly. `completed`
describes the startup transaction only. The report always sets
`review_completion_assessed` to `false`.

### How the estimate works

For a pending draw, the journal supplies the baseline paths and expected
manifest-bound digests. The helper examines source and destination **metadata**.
It does not read those source or baseline contents to verify their hashes.

- `missing_baseline_bytes` counts missing baseline files, rounding each logical
  size up to the destination allocation block. This is a minimum baseline-copy
  amount under the declared model; it excludes possible replacements and other
  overhead.
- `copy_bytes_upper_bound` includes every candidate baseline file, including
  existing files whose hashes remain unverified. Matching file sizes do not
  prove that a baseline can be reused.
- For `unstarted`, the guaranteed global canonical file supplies the minimum,
  while **all manifest-listed repository files** supply a conservative upper
  estimate. This avoids selecting or predicting an assignment. It may overstate
  the actual startup cost substantially.
- Missing directories contribute one modeled block each. The inode estimate
  includes missing candidate files/directories, one staging inode and five small
  control-record inodes. Actual control-record bytes and further metadata
  growth rely on the configured reserve.
- File sizes use logical bytes, rather than existing `st_blocks`, because a
  sparse or compressed source may be copied densely.
- Staging and the final baseline share a file allocation after atomic rename;
  their bytes are not counted twice. Split staging/baseline filesystems are
  refused.

The known userspace hashing cost is the largest whole source or existing
baseline file that official startup may read into memory. For tmpfs, the model
adds the **new** baseline/directory allocation to that hash buffer and the
reserve. Existing tmpfs contents have already reduced observed memory
headroom. Disk and memory are independent constraints; their free capacities
must not be added together.

Visible cgroup headroom is calculated separately at each measured level as
`max(0, memory.max - memory.current)`, then the minimum finite headroom and host
`MemAvailable` are used. An unreadable visible cgroup level makes the result
indeterminate even if host memory appears plentiful.

These are modeled allocation bounds, not filesystem-wide physical-byte bounds.
Quotas, concurrent consumers, filesystem metadata, copy optimizations, hidden
cgroup limits, and Python/JSON/runtime peaks are not measured fully. Reserves
are allowances, not measured peak usage. The helper reads at most 32 MiB for a
manifest and 4 MiB per assignment/journal; parsed metadata also consumes memory.
Independently verify the issued packet using its official verification command.

## Preserve an interrupted draw

Choose a **new directory outside `WORK` whose parent already exists**. Use
storage that survives the runtime if persistence is required.

```sh
python3 start_capacity.py checkpoint-pending \
  --work /path/to/packet/WORK \
  --out /path/to/checkpoints/pending-001

python3 start_capacity.py verify-checkpoint \
  --checkpoint /path/to/checkpoints/pending-001
```

The checkpoint contains exact original bytes for:

- `PACKET-MANIFEST.json`;
- `pending-main-draw.json`, copied from `WORK/.review/`;
- `ASSIGNMENT.json`, only if it was already published and matches the journal;
- `CHECKPOINT.json`, this helper's hash/size inventory and scope receipt.

“Opaque” means the helper preserves original bytes and does not reinterpret
task semantics. It checks JSON structure, packet binding, seed encoding,
assignment identity, baseline-path safety, and manifest digest bindings. It
does not validate the review engine's task-selection or question-selection
semantics. SHA-256 verifies consistency of the saved bytes; it does not
authenticate an untrusted packet.

Copies use exclusive creation, file flush/fsync, saved-byte verification, and
a final comparison against the source records while the official lock is held.
The success receipt is published atomically after those checks and checked
again; a failed final verification withdraws that newly created receipt. Existing
destinations are refused, including aliases resolving inside `WORK`. On a
copy failure, partial output is retained without a success receipt. A directory
without a verifiable completed `CHECKPOINT.json` is not a completed checkpoint.
The receipt records whether checkpoint-directory and parent-directory fsync were
available; storage durability
still depends on the underlying filesystem. tmpfs remains volatile.

### Recovery boundary

**This helper implements no restoration or replay.** Its checkpoint schema is
not accepted by `resource_guard.py restore`, which expects a completed-assignment
checkpoint with a different schema. The helper does not certify a replay
procedure or write these saved files into a fresh packet. Retain the checkpoint
with the exact original packet and workspace for an explicitly validated
recovery procedure. Do not fabricate a replacement seed or assignment from it.

No baseline source files, solve artifacts, check evidence, runtime environments,
or completed-review records are included in this checkpoint.

## Synthetic verification

Run the entire standalone suite from this directory:

```sh
python3 -B -m unittest discover -v
```

All fixtures live in temporary subdirectories here and are removed after tests.
The suite does not open an issued packet. It covers metadata-only behavior,
state transitions, same-size corrupt baselines, dense sizing for sparse files,
independent block/inode exhaustion, tmpfs memory accounting, visible ancestor
cgroup limits, unknown/malformed measurements, exact checkpoint bytes, hash
tampering, path aliases, active locks, source mutation, and injected write
failure. `TEST_RECEIPT.json` and `test-output.txt` record the final run.

## Suggested upstream work

The official startup currently includes the complete canonical JSONL file in
the immutable baseline and makes a physical staged copy. Its verification
paths also use whole-file reads. A focused upstream change could add a startup
capacity preflight and stream hashes in bounded chunks. Exact pending-journal
checkpoint support should remain distinct from completed-assignment recovery.
This companion proposes and demonstrates those resource/recovery boundaries
without modifying the issued implementation.
