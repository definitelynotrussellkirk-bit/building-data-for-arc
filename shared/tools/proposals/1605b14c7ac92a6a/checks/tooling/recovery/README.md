# Sparse packet extraction recovery

`sparse_packet.py` uses only Python's standard library. It is a separate recovery
utility; it never edits the packet's helpers, manifest, or assignment contracts.
Task programs, rules, notes, and private data are treated only as opaque source
bytes for hashing and copying. No task contents are printed.

## Initial extraction and official draw

Choose a new target with sufficient capacity, then run:

```bash
python recovery_tools/sparse_packet.py ORIGINAL.zip TARGET --draw
```

Without `--draw`, extraction stops before invoking the assignment API. To perform
the draw later, rerun this same command with the same ZIP and target plus `--draw`.
Do not run an independent random `review.py start` between these steps.

The utility verifies the entire ZIP against its canonical manifest, including
both outer entry files, using streaming hashes. It validates member paths,
rejects symlinks and special file types, and checks the bundled Racket archive's
pinned hash. It durably saves one 32-byte random seed under `TARGET/.recovery/`
before deriving task IDs. Every retry reuses that seed and rejects a different
ZIP or manifest. Existing files must match their issued source hashes; changes
are never overwritten.

The selected full main and blind task directories, official task-filtered runtime
dependencies, catalog, generic sources/docs/guides/tests, chosen question, root
helpers, and bundled Racket archive are materialized. The explicit `--draw` flag
then calls the unmodified official `draw_main` API with the saved seed. Its
existing journal handles interrupted draws. Default operation never calls any
generator or prepares a solve.

## Resume and additional tasks

After an interruption, rerun the same command. Do not remove or replace the saved
seed. Previously completed copies are checked and reused. Publication is atomic;
the utility removes only temporary files it creates during the current call.
It never removes existing task data.

For audit tasks that the official audit command has already assigned:

```bash
python recovery_tools/sparse_packet.py ORIGINAL.zip TARGET --task AUDIT_ID_1 --task AUDIT_ID_2
```

This hydrates those task directories and their declared runtime dependencies.
It never selects audit tasks or draws another assignment. Earlier hydrated task
IDs are retained in cumulative receipts.

Once a completed official assignment matches the saved seed, explicit `--task`
hydration preserves edits to previously materialized main-baseline candidate
files: the main task directory, canonical ledger, and bound archival authority.
Those files must still be regular files. Shared sources and all other selected
sources remain hash-checked. Before a completed draw, all existing sources remain
strictly hash-checked, including during `--task` hydration. Ordinary resume without
`--task` is always strict; use the explicit hydration command after making repairs.

## One-time audit assignment in a sparse workspace

Once the main generator work is complete, the official audit command needs both
selected original sources present before it can save its random assignment. Use
the explicit recovery mode to prevent an extraction failure from losing that draw:

```bash
python recovery_tools/sparse_packet.py ORIGINAL.zip TARGET --audit-draw
```

This requires the existing completed main assignment, blind assignment, saved
main seed, and materialization receipt. It durably publishes an independent
32-byte random audit seed in `.recovery/audit-seed.json`, bound to the original
ZIP and manifest, before deriving either audit target. It calls the official
`audit_ids_for_seed` with the blind task excluded, hydrates exactly those two
additional task directories and their declared dependencies, and commits a new
immutable cumulative source receipt before calling unmodified official
`draw_audit(WORK, seed=saved_audit_seed)`. Main edits are preserved as in explicit
`--task` hydration. Ordered task IDs, packet identity, seed, and source hashes are
checked against the persisted official contract. Output includes its hash and the
new materialization receipt head hash, but never prints a seed.

Repeat `--audit-draw` only to resume/verify the same saved audit selection; it never
rerolls. It cannot be combined with `--draw`, `--task`, or `--verify-archive`. An
existing audit assignment without its recovery seed is rejected. Because the
official audit writer is not atomic, a truncated contract from an external disk
failure is preserved and reported as an error; the wrapper does not overwrite it
or create a different assignment. Keep the saved audit seed and earlier receipts
for explicit recovery if that condition occurs.

## Durable evidence

`TARGET/.recovery/seed.json` binds the seed to the original ZIP and manifest hashes.
Each successful phase creates a new immutable `materialization-NNNNNN.json` snapshot
containing the cumulative exact original source path/hash inventory. Snapshots
link to their predecessor by filename and SHA-256. The atomic `extraction.json`
file points to the latest snapshot and its hash. Subsequent hydration checks the
complete snapshot chain and monotonic inventory. Keep these files with recovery
evidence and pin the latest receipt hash before any archive-backed packaging.

The tool prints only paths, selected IDs, hashes, counts, and sizes. Save stdout
if a command record is needed. It does not print the seed.

## Verification without extraction

```bash
python recovery_tools/sparse_packet.py ORIGINAL.zip --verify-archive
python -m unittest discover -s recovery_tools -v
```

`--verify-archive` creates no target or seed. Synthetic tests cover unsafe member
paths, changed archive bytes, tampered source hashes, interrupted seed reuse,
changed local sources, destination symlinks, additional task hydration, immutable
receipt lineage, and preservation only after the draw.

## Resource and packaging limits

The original packet's common selected-runtime sources are about 84 MB; the
bundled Racket archive adds 34 MB, its installation about 129 MB, and a temporary
runtime snapshot another 84 MB. The draw also copies the selected baseline,
including the 21.6 MB canonical ledger. Allow space for checks and results.
The standard runtime uses Python's temporary-directory location, so a task-owned
`TMPDIR` can direct snapshots to a filesystem with adequate capacity.

A sparse workspace cannot pass the official full-tree `review.py verify` or
standard return-packager missing-source checks. Archive verification is accurately
reported separately. Do not suppress those checks or claim that a sparse tree
passed full-tree verification. The original ZIP and materialization receipts
must remain available for full extraction or a separately reviewed archive-backed
packaging recovery workflow.
