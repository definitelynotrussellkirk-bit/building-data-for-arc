# Proposed packet subset helper

`packet_subset.py` is an optional, standard library helper for the issued
`arcpuzzles-full-packet-v2` archive format. It addresses the observed full
extraction `OSError: [Errno 28] No space left on device` with roughly 100,000
members. It leaves the normal review, solve, assignment and packaging scripts
unchanged. It performs no disk or memory capacity preflight and no archive or
checkout cleanup.

## Commands

Requires Python 3.11+ on a POSIX system (`fcntl` locking and exclusive hard-link
publication are used). Copy this directory, or just `packet_subset.py`, beside
the original ZIP. Paths below are examples; run the helper from any directory.

```sh
# Hash every ZIP file, without extracting it or printing its contents.
python3 packet_subset.py verify ORIGINAL.zip

# Create one random 32-byte seed, journal it, and extract its initial subset.
python3 packet_subset.py extract ORIGINAL.zip review-work

# Same command resumes the saved seed and unchanged files after interruption.
python3 packet_subset.py extract ORIGINAL.zip review-work

# Complete the official draw using the helper's exact pending contract.
cd review-work
python3 review.py start
```

After `start`, follow `review.py`'s blind-solve-first directions. The helper
copies and hashes source bytes internally but never prints generator, rule,
notes, canonical examples or private solve contents. It does not prepare a
solve, run a generator, or run a reference rule.

For a previously recorded seed, `extract --seed HEX` accepts exactly 64 hex
digits. That option supports reproducible recovery and compatibility testing.
An explicit seed that differs from the saved seed is rejected. A torn or
invalid seed journal is rejected rather than replaced. Keep the journal for
recovery; deleting it defeats the no-reroll guarantee.

Add the closures of **already assigned** audit targets by ID:

```sh
python3 packet_subset.py add ORIGINAL.zip review-work --task FIRST_ID --task SECOND_ID
```

`add` also accepts an existing subset created without this helper when its
packet manifest, outer entry files and complete `ASSIGNMENT.json` match the
original packet and seed. It adopts that seed. It does not draw audit targets,
create an audit assignment, or alter an existing main assignment. Obtain IDs
from the existing audit contract; this proposal does not change the official
audit draw's own recovery behavior.

## Complete the original inventory before official packaging

The official return builder checks every original `repo/` file. A runtime
subset can run its selected checks but **cannot be packaged directly**. After
the selected work is finished, hydrate the missing originals before running
the normal packaging command:

```sh
# Read-only inventory counts; does not query free space or memory.
python3 packet_subset.py complete ORIGINAL.zip review-work --deduplicate --dry-run

# Restore every still-missing original member, preserving all existing files.
python3 packet_subset.py complete ORIGINAL.zip review-work --deduplicate

cd review-work
python3 review.py package
```

`complete` verifies the packet identity and existing main/pending assignment.
It verifies every restored member's original hash. Within this invocation,
newly restored files with identical original SHA-256 values share a hardlink.
Every representative comes from a newly streamed and verified ZIP member;
existing files are never chosen as representatives, even if their bytes match.
Existing selected files, reviewer edits and existing file permissions are
preserved. On a retry, previously restored files count as existing and are
also left untouched.

Restored files have read-only permission bits (`0444`), including all members
of each new hardlink group. Treat these as immutable reference material. If
you later need to edit a restored file, replace it with an independent copy
first; changing permissions or writing through a privileged process does not
break a hardlink. Complete hydration is intended after active selected-source
work. This approach reduces new payload inode use to the number of distinct
missing-file hashes; directories still require their own filesystem entries.

Completion records counts and changed existing paths in
`.packet-subset/completion.json`, with a compressed, exact inventory of all
original paths in `.packet-subset/completion-inventory.jsonl.gz`. It does not
alter the original manifest or relax the official return builder. The
`--dry-run` output reports original and missing file, unique-hash and parent
directory counts; it performs no writes. No live completion was performed by
this proposal's test harness.

The main reviewer subsequently ran completion on the live review workspace.
The retained `completion.json`, `completion.console.log`, and
`completion-inventory.jsonl.gz` record 94,387 restored files, 69,972 new
payload inodes, and 24,415 hardlinks. The full original inventory was hashed,
and the existing generator and selected-authority edits were preserved. This
is separate from the isolated harness above. Completion can remain quiet
while payloads are flushed and the final inventory is hashed; it prints its
JSON summary after finishing.

## Selection and integrity

The selection formulas and pending contract mirror `review_full_draw.py`:
main pool order is preserved; question and blind selections use the official
SHA-256 seed suffixes; assignment identity and complete baseline hash bindings
are identical. The helper writes the official pending journal **before** any
payload extraction. `review.py start` resumes it, so the main draw cannot
silently choose another task.

The dependency boundary is a small port of
`review_replay._runtime_members`, unioned across the repair target, blind target
and any added targets. It includes all files under those generator homes and
their rule-identity homes, mapped shared runtime files, the canonical corpus,
bound reference sources, the Python review runtime, catalogs, vendor assets,
bootstrap files and outer entries. The helper additionally includes the
question files, supplied guides and selected documentation. It does not copy
every unrelated task's evidence or tests. This is an initial runtime subset,
not a claim that the entire original packet was extracted.

The original canonical manifest must describe the exact ZIP file inventory.
Every copied member is streamed through SHA-256 and installed only after its
original hash matches. All selected archive members are reverified on rerun,
including those whose destination already exists. `verify` checks *all* ZIP
members, including unselected members. The manifest binds the contents within
the supplied archive; it is not an external signature authenticating the
archive's origin.

Unsafe, duplicate or noncanonical paths, symlink/special/encrypted ZIP members,
file-as-directory collisions and destination symlinks are rejected. File
publication is exclusive and never replaces an existing checkout file. Use a
destination that another process is not editing during extraction; the lock
coordinates concurrent invocations of this helper, not arbitrary programs.

`extract` stops if an existing selected file differs from the issued bytes.
`add` preserves such edits, extracts missing files, and reports the differences
in `preserved_modified`. Neither command restores reviewer changes. Successful
extraction leaves `.packet-subset/inventory.json` with each present original
member's exact path, size, actual SHA-256 and original SHA-256; its counts are
recomputed from the destination. Review-created files such as solve outputs,
baselines and notes outside the original archive inventory are not copied into
that inventory. JSON summary output contains no source text.

The helper removes only temporary staging files created by its own atomic
writes. It never deletes a ZIP, checkout, baseline, prior receipt, partial
payload file or user-created file. Ordinary extraction failures leave the
saved seed and completed payload files available for a rerun.

## Verification

Synthetic tests are reproducible without the real archive:

```sh
python3 -m unittest -v test_packet_subset.py
```

The tests cover full hash verification and tampering, exact selected filenames,
same-seed selection, byte-exact official pending JSON, unchanged reruns, an
injected `ENOSPC`, selection failure before extraction, corrupted journals,
preservation of reviewer edits, adoption of an existing subset, ZIP traversal,
duplicates, symlinks and file/directory collisions. Completion tests additionally
check read-only hardlinks between new originals, inode separation from existing
selected files with identical bytes, preservation of edits, unchanged reruns
and a dry run with no filesystem changes.

The real-archive compatibility harness uses an existing assignment seed and
creates only its own temporary checkout:

```sh
python3 verify_actual.py ORIGINAL.zip EXISTING_WORK/ASSIGNMENT.json
```

It records exact subprocess commands and exit codes, verifies the full archive,
extracts a subset, checks the pending contract against the existing assignment,
runs the official `review.py start`, checks the official blind-selection and
runtime-closure functions, and verifies an unchanged extraction rerun. It
records before/after archive and input-assignment hashes, saves a compressed
exact extraction inventory, then removes only its own temporary checkout. It
does not exercise generation or Racket execution.

See `actual-verification.json`, `actual-extraction-inventory.json.gz` and
`unit-verification.json` for measured results. `completion-dry-run.json` records
the read-only complete-hydration plan for the live subset at the time measured.
`actual-verification-first-attempt.json`
retains the caught pending-JSON formatting failure and its diagnosis; the
current helper includes the regression fix. This remains a proposed utility,
with no change to the packet's production runtime or assignment machinery.
