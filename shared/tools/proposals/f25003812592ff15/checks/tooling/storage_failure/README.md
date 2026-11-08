# Optional storage diagnosis proposal (F1)

`diagnose_storage.py` is a standard-library, read-only CLI for investigating an
observed `ENOSPC` error. It calls `os.statvfs` once per requested path and prints
JSON to stdout. It performs no recursive scan, deletion, relocation, write test,
or automatic capacity gate, and has no third-party dependency.

```sh
python3 diagnose_storage.py /path/to/existing/workspace /path/to/alternative
```

Each path reports block and fragment sizes, free and available bytes, and free
and available inode counts when the filesystem reports a meaningful positive
inode capacity. Byte calculations use `f_frsize`, falling back to `f_bsize` if
the fragment size is zero or absent. Zero or unreported total inode capacity is
treated as unavailable information, rather than proof of inode exhaustion.

`enospc_explanation` is `bytes`, `inodes`, `both`, or `neither`, according to the
available counters. `unknown` means there is no measured exhaustion and at least
one necessary counter is unavailable. `evidence_complete` identifies partial
statistics. A known exhausted resource is still reported when the other counter
is unknown. `neither` means the snapshot does not explain the failure; it does
not establish that a write will succeed. Filesystem errors retain their type,
errno and message in JSON. A missing `statvfs` API is reported as unavailable.
Exit status is 0 when every path's statistics were read, 1 when a path failed or
the API is unavailable; an exhausted but successfully inspected filesystem is
still a successful diagnostic invocation.

## Actual failure that motivated the proposal

During this review, creating
`/workspace/scratch/bc2ac8d91725/review/WORK/checks/audit/341758fa9de1/` failed:

```text
mkdir: cannot create directory '.../WORK/checks/audit': No space left on device
```

At that time, `df -h /workspace/scratch/bc2ac8d91725/review` reported **14 GB
available**, while `df -i` reported **2,097,152 total inodes, 2,097,152 used,
zero free**, or 100% inode usage. The error was therefore consistent with inode
exhaustion despite ample bytes. The original input and extracted workspace were
preserved, and work continued from a complete copy at
`/dev/shm/bc2ac8d91725/review`, with temporary snapshots directed to a local tmp
directory there. This was an explicit operator action; the proposed CLI does
not make that decision or copy anything.

`live-diagnosis.json` contains an actual later invocation against both paths.
It is a fresh measurement, not a reconstruction of the earlier failure. At
that invocation the original filesystem had 75,767 available inodes and the
alternative had 1,153,024; both reported `neither`. Capacity had changed since
the failure, so these readings must not be cited as measurements of its earlier
state. Neither the historical observation nor live readings are hardcoded into
the CLI.

## Verification and reproducibility

The six focused stdlib tests cover the four exhaustion categories and unknown
evidence; available versus free counts; fragment-size byte conversion;
unreported inode capacities; OS error preservation; unavailable `statvfs`; and
a real CLI invocation returning JSON for a mixed successful/missing path pair.
The test command ran **6 tests, all passing**, exit 0. The same six tests were
first run before the CLI existed and failed with the explicit missing-feature
assertion, exit 1. No repository-wide test claim is made for this isolated
proposal.

From `/dev/shm/bc2ac8d91725/review`:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/bc2ac8d91725/tmp python3 -m unittest discover -s WORK/checks/tooling/storage_failure -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/bc2ac8d91725/tmp python3 WORK/checks/tooling/storage_failure/diagnose_storage.py /workspace/scratch/bc2ac8d91725 /dev/shm/bc2ac8d91725
```

The live CLI command exited 0; its stdout is retained in
`live-diagnosis.json`. Exact argv arrays, cwd relative to WORK, environments,
exit codes, test counts and the test output summary are in `commands.json`.
This directory is a reusable proposal for feedback item F1; shared tools were
not modified.
