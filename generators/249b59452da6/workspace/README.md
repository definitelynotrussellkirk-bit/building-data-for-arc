# Reusable task-contract probe

`contract_probe.py` is an optional, task-local diagnostic tool. It discovers
the actual rival and witness declarations from `../generator.py`, checks their
canonical fit, and retains source hashes and complete compressed evidence. It
does not alter shared gates, label training examples, or approve the generator.

From the extracted packet root, the final full run was:

```bash
python3 run_with_racket.py python3 -B generators/249b59452da6/workspace/contract_probe.py --out ../checks/contract-final --joint --racket --exhaustive-racket --per-band 100 --require-teaching-support
```

Use a new output directory when reproducing a run. The wrapper executes its
payload from `repo`. For fast iteration, omit `--joint`, `--racket`, and
`--exhaustive-racket`, or lower `--per-band`. Run `--help` for all controls.

## What it checks

- Exact dimensions, original-input eligible-window count, palette, sparsity,
  deterministic repeats, and consistency with the public observer.
- Every one-axis integer request, invalid/misspelled controls, and optionally
  all 9,000 dimension/count/palette combinations at one fixed seed and index.
  Structured refusals are recorded, never counted as successful grids.
- Canonical inputs and explicit malformed/negative validator cases.
- The generator's actual `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`,
  `LESSON_COMPETITORS`, and witness mappings. Rival lists are discovered, not
  duplicated in the probe. Claimed canonical shortcuts must fit every pair.
- Every consecutive four-input window in each sampled sequence, holding out
  each input once. With 100 inputs in four bands this is 1,552 rotations from
  400 sampled inputs; overlapping windows are not additional unique inputs.
- With `--require-teaching-support`, at least two distinct demonstration input
  hashes must refute each declared canonical-fitting shortcut. This also catches
  rivals that agree on the query, separately from query-disagreement ambiguity.
- Optional public `Catalog.apply` parity against the unchanged canonical Racket
  authority, including all 729 2x3 grids over colors {0,2,7} when requested.

The default oracle is independently written Python and is explicitly diagnostic.
`--racket` records actual authoritative execution separately. Racket mode needs
its library Catalog layout and fails explicitly in unsupported layouts; ordinary
Python checks and task tests locate either supported layout with public
`reviewer_support` helpers.

## Evidence and failure behavior

`report.json` identifies the generator and probe SHA-256 values, sampling policy,
all denominators, source stability, failure counts, and compressed artifact
metadata. `cases.jsonl.gz`, `failures.jsonl.gz`, and optional
`racket_batches.jsonl.gz` preserve full grids and decisions. Each includes the
uncompressed hash, byte count, record count, and restoration command in the
report. No failures are dropped to reduce return size.

Artifact-integrity failures after stream closure remain in
`report.json.finalization_failures`. Closed gzip streams are not reopened or
rewritten; a dedicated regression forces that path. The tool exits nonzero on
errors, hook failures, unsupported execution, or requested teaching-policy
failures. A finite pass is not a claim about arbitrary seeds, unrestricted
domains, undeclared rivals, or measured model training gains.

## Focused tests

`tests/test_review_contract.py` retains the baseline failures and covers exact
controls, validator behavior, canonical authority, and rotating lessons.
`tests/test_review_motifs.py` independently checks both shortcuts found in final
review. `tests/test_contract_probe.py` tests diagnostic geometry, rival discovery,
teaching-support behavior, compressed integrity, and failure finalization.

Use the supported task stage from the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 249b59452da6 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

The payload interpreter must have pytest available with its user site disabled,
because the task worker isolates user-site imports. The review used a private
venv with the installed test dependencies; the packet's
`checks/repository-tooling-diagnosis/` records that environment-only remedy.
