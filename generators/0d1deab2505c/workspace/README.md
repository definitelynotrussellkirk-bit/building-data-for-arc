# Reusable reviewer tools

These are authoring tools with reference labels. Keep them closed during any
visible-only solve.

## Exact transport and rival probes

From WORK:

    python3 run_with_racket.py python3 generators/0d1deab2505c/workspace/probe_transport.py --out ../checks/transport-replay

Use a new output directory. The tool independently places four expected fixtures
(straight tail, asymmetric tail, mixed creatures, lawful arm-color permutation),
adds an exactly replayable generated input, invokes public Catalog.apply, and
iterates current rival declarations. It records reference errors separately from
wrong outputs and checks each declared canonical shortcut against all usable pairs.

## Reversible JSON evidence compaction

From WORK:

    python3 repo/generators/0d1deab2505c/workspace/compact_evidence.py compact checks/REPORT.json --receipt checks/REPORT-format.json
    python3 repo/generators/0d1deab2505c/workspace/compact_evidence.py restore checks/REPORT-format.json --out checks/REPORT-original.json

The output and receipt must be new where requested. Only a recognized indent=2
JSON encoding is accepted. No keys, values, grids, failures or source bindings are
dropped. The original byte sequence is reconstructed and compared before the file
is compacted; the receipt retains original and compacted SHA-256/size plus exact
format settings. Restore without --out verifies reconstruction without writing.

This return's 300-lesson census shrank from 12,584,775 to 2,501,585 bytes. The original
SHA-256 is dea046e7d4bcf3883ca9a567c9a1ce42cb32a6473f2ce746bf0b796de49ebd02.
checks/lesson-census-format.json and checks/evidence-compaction-verification.json
record successful byte-exact restoration. Unchanged failed battery receipts remain
in their original representation.

## Focused tests

Use the packet's public task_tests stage. The task's tests use reviewer_support
canonical helpers and public Catalog.apply, and run in a portable staged runtime.
See RESULTS.json for the exact selected Python interpreter and executed command.
