# ARCpuzzles packet recovery toolkit

**The attached packet is internally consistent. The assigned review is blocked by the runtime's writable capacity.**

This toolkit accompanies `SEND-THIS-ARCpuzzles-review(20261019-122009).zip`. It contains a working streaming verifier and resumable extractor, 25 passing unittest methods, exact receipts, and source-bound findings about the packet's recovery constraints. It is a standalone tooling deliverable. No generator repair was selected, implemented, tested, or approved.

## Verified results

| Check | Observed result | Evidence |
| --- | --- | --- |
| Issued archive integrity | 78,750 files verified against expected SHA-256 values and ZIP CRCs | `evidence/archive-verification.json` |
| Workspace manifest inventory | 78,747 workspace files, two outer entry files, and the manifest itself | `evidence/archive-verification.json` |
| Full archive size | 249,581,752 compressed bytes; 1,133,563,806 uncompressed bytes | `evidence/archive-verification.json` |
| Extraction footprint | 50,197 implied directories; 128,947 file/directory entries before runtime and review artifacts | `evidence/archive-verification.json` |
| Tool tests | 25 unittest methods passed, including codec subcases and injected ENOSPC | `evidence/tests-final.log` |
| Final real extraction | 6,256 files published, then exit 2 / errno 28 / no space left | `evidence/extraction-final.json` |
| Assignment | Not drawn; no assignment or pending draw record present | `evidence/final-workspace-state.json` |

Archive SHA-256:

`4fb8f937c82637a8b4dad464944bd5b476fdf5a8aa97b4b3696a30435db1bfe9`

Manifest SHA-256:

`b8eb7543d02d210bb13ceda779bdfecb973978d372bfe4326ec2114573edc9ab`

These checks establish consistency of the supplied archive and its own manifest. They do not execute or validate a puzzle rule, certify generator quality, or replace the packet's original verification and review commands.

## What the tool does

`arc_packet_recover.py` uses Python 3.12+ and the POSIX standard library. It requires a filesystem supporting directory file descriptors, no-follow opens, file locks, and hard links within a directory.

- Streams file payloads in 1 MiB chunks and checks every archive member's checksum.
- Checks canonical manifest encoding, exact member inventory, path safety, duplicate names, and ZIP file types.
- Verifies the complete archive before extracting any member.
- Records the exact archive and manifest identity in the destination.
- Inspects every existing packet file before writing any archive member. Byte-identical files are reused with their inode and modification time preserved.
- Refuses to overwrite reviewer edits, use a destination belonging to another archive, or follow destination symlinks.
- Publishes a member only after its complete content is copied, hashed, flushed, and synced. A no-overwrite hard link makes publication atomic.
- Retains completed files after an ordinary I/O failure and removes the current operation's unpublished temporary file.
- Emits structured JSON on stdout for handled archive, destination, and I/O failures. An optional report-write failure preserves the primary stdout result.

The program does not execute packet code, install dependencies, draw an assignment, invoke Racket, inspect answers for solving, or remove existing reviewer files. It performs no disk-capacity preflight.

## Continue in the existing workspace

The partial extraction is:

`/workspace/scratch/a9d83d86b63f/packet`

Its recovery identity is bound to the original ZIP. After writable capacity is available, run the following from the directory containing this toolkit:

```bash
python3 arc_packet_recover.py extract \
  '/workspace/scratch/a9d83d86b63f/upload/SEND-THIS-ARCpuzzles-review(20261019-122009).zip' \
  '/workspace/scratch/a9d83d86b63f/packet' \
  --report resume-122009-2.json
```

Keep the same original ZIP and destination. If another interruption occurs, repeat extraction with a new report filename, or omit `--report`. The tool checks and reuses completed files; it never selects a task.

Once extraction exits successfully, run the packet's original commands **in that extracted packet directory**, in order:

```bash
cd '/workspace/scratch/a9d83d86b63f/packet'
python3 review.py verify
```

Only after that command succeeds:

```bash
python3 review.py start
python3 review.py duties
```

Follow the resulting duties, including any blind solve before opening generator, rule, note, or audit contents. Preserve that workspace and any journaled assignment when resuming later.

## Use in another workspace

Retain the original ZIP and this small toolkit. Use a fresh destination with room for the full extraction, baseline copies, bundled runtime, and subsequent checks:

```bash
python3 arc_packet_recover.py verify \
  'SEND-THIS-ARCpuzzles-review(20261019-122009).zip' \
  --report verify-122009.json

python3 arc_packet_recover.py extract \
  'SEND-THIS-ARCpuzzles-review(20261019-122009).zip' \
  './arc-review-122009' \
  --report extraction-122009-1.json
```

Then run the original `review.py verify`, `start`, and `duties` inside `arc-review-122009`, as above. The original archive is intentionally not duplicated in this toolkit.

## Exit codes and receipts

| Exit | Meaning |
| --- | --- |
| 0 | Requested verification or extraction completed, and any requested report was saved. |
| 1 | Invalid archive, manifest, member inventory, path, checksum, or compressed payload. |
| 2 | I/O failure, or an optional report could not be saved. Read stdout for the primary operation result and stderr for a report warning. |
| 3 | Destination conflict: different archive identity, changed existing file, unsafe path, or another recovery process's lock. |

Reports use create-only publication. They never overwrite a previous report. Use distinct report filenames for successive runs.

## Validation and limits

Run the complete standalone suite from the toolkit directory:

```bash
python3 -B -m unittest discover -v
```

The tests exercise real synthetic ZIPs and real filesystem behavior. The one disk-full injection substitutes an ENOSPC failure at a file-copy boundary; it verifies that already-published files survive, the incomplete member is absent, temporary output is cleaned, and a subsequent unpatched run completes. Additional tests cover reviewer edits, changed ZIP identity with identical member contents, traversal, multiple symlink positions, malformed archives, DEFLATE/BZIP2/LZMA corruption, and report/source symlink loops.

The first full-archive verification process was terminated with signal 9 under severe runtime memory pressure. The diagnostic snapshot showed memory usage close to the 8 GiB cgroup limit and existing OOM kills. The exact cause of that individual signal is not independently proven. The implementation was then changed to compare canonical JSON incrementally, reuse path strings, and release irrelevant parsed metadata. A subsequent full verification completed in 21.665487 seconds. The final source also completed full archive verification before publishing the 6,256 files in the last extraction attempt.

Streaming payloads does not mean constant total memory: the ZIP central directory and manifest still require memory proportional to the file inventory. A hard process kill can leave an unpublished temporary file; the tool does not delete unknown files on a later run. Its lock coordinates other instances of this helper, not arbitrary concurrent writers. Use an exclusive destination while extracting. After intentionally editing a review, use the packet's own review/check resumption mechanisms; this helper refuses to overwrite changed issued files.

The complete real packet was not extracted, and the native verifier, assignment, generator batteries, task tests, both audits, both solves, final patch replay, and official return builder were not run. `RECOVERY_STATUS.json` records those boundaries.

## Contents

- `arc_packet_recover.py`: reusable implementation.
- `test_arc_packet_recover.py` and `test_recovery_regressions.py`: complete synthetic test suite.
- `SOURCE_FINDINGS.md`: why sparse extraction cannot satisfy the issued workflow.
- `FEEDBACK_TO_CODEX.md`: concrete future-agent tooling suggestions.
- `RECOVERY_STATUS.json`: machine-readable handoff.
- `evidence/`: exact commands, hashes, passing and failing test records, archive verification, and environmental failure receipts.
