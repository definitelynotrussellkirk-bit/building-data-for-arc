# F1: Optional recovery tooling for source-bound packets under ENOSPC

This is a reusable tooling proposal retained as check evidence. It is separate
from the selected generator repair and is not a shared-source patch. The shipped
helpers, assignment contracts, manifest, and source-scope allowlists are unchanged.

## Recovery behavior

`sparse_packet.py` streams the original ZIP against its canonical manifest,
validates outer entry hashes and safe regular member paths/types, and materializes
a selected physical closure. It saves a random 32-byte main seed durably before
deriving the main selection. Explicit `--audit-draw` saves an independent audit
seed before deriving its two targets, excludes the persisted blind task, hydrates
their original sources, commits an immutable cumulative receipt, then calls the
unmodified official audit draw with that same saved seed. Retries reuse saved
bindings and seeds; changed archives, shared sources, history, and conflicting or
partial contracts fail closed. It never silently rerolls or replaces edited
sources. Earlier materialization receipts remain hash-linked and cumulative.

## Explicit alternate archive verification

A sparse workspace cannot honestly pass the official physical full-tree check.
`archive_package.py` is an explicit alternate archive-backed workflow: the original
ZIP, prior materialization receipt SHA, workspace, destination, and separate
verification-receipt destination must be supplied. It verifies all original
archive bytes, every receipt-history binding, every physically materialized
original, and the exact frozen selected baseline. An intentionally omitted source
cannot conceal deletion of a previously materialized source. Physical symlinks,
undeclared source additions, changed shared bytes, unsafe candidate permissions,
and edits outside the original selected scope remain blockers.

No allowlists or official source-scope restrictions were removed. The archive
adapter imports the hash-pinned original generic return helper from the verified
ZIP, retains official delta/canonical-row restrictions and return assembly, and
still runs the official final return validator and ZIP budgets. Equivalence tests
compare the resulting ZIP bytes with the official full physical-tree builder on
synthetic fixtures. Reports must retain the explicit archive-verification mode;
`full_tree_verify_supported` remains false for sparse extraction. This tooling
does not make the official physical-tree verification pass or approve a generator.

## Retained verification and provenance

A final preflight exposed that Python 3.12's standard zipimport could not index
this issued 76,129-member ZIP64 packet even though zipfile could read it. The
archive adapter now uses a private source-only verified-ZIP importer: every
imported helper's raw bytes must match its original manifest hash before compile,
cached overlay packages are rejected, and the original return-helper SHA pin and
assembly remain intact. A regression streams and verifies the actual original
packet before loading its helper sources through that importer.

After that correction, the final executed command was:

```bash
env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm /workspace/scratch/89096ac2a867/review-venv/bin/python -m unittest discover -s recovery_tools -p 'test_*.py' -v
```

It ran from `/workspace/scratch/89096ac2a867` under Python 3.12.14 and exited 0:
44 tests in 15.968 seconds (29 archive-packaging tests, 15 sparse/audit recovery
tests). Actual final combined test output and exact command/environment/source
hash receipt are copied byte-for-byte under `tests-44/`. These tests include the
actual large ZIP64 packet regression and official full-tree assembly equivalence.
No optional tests were rerun merely to prepare this proposal.

Earlier evidence remains unchanged: the prior 41-test command exited 0 in 11.375
seconds; its merged tool-output transcription and explicit provenance caveat are
under `tests-41/`. A separately captured stdout/stderr pair for that historical
41-test run is unavailable. Original earlier 36-test stdout/stderr files remain
byte-identical under `tests-36/`, with their known provenance. The original
`ENVIRONMENT_FAILURES.json` records both failed full extractions. Historical
receipts refer to their own earlier source hashes and are not substituted for
the final corrected-source 44-test result.

## Current outstanding packaging requirement

The working session currently uses a temporary symlink at the vendor Racket
archive location to relieve storage pressure. Restore the original regular
`WORK/vendor/racket-minimal-8.10-x86_64-linux-cs.tgz` before packaging; its pinned
upstream SHA-256 is
`2c5fdc02787ba569f03d89cad6086a5c3be49045d58281e2db7fe31b43650eb7`.
Do not alter the manifest or bypass the symlink/source-integrity checks. This
proposal does not restore that archive or perform the final packaging operation.
