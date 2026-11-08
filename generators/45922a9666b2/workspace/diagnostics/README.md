# Safe preparation diagnostics: optional shared-tool proposal

## Finding

`review_solve.prepare_solve` records only the exception class publicly. Worker
exceptions can contain a private Racket rule, so printing exception messages or
tracebacks is inappropriate during a visible-only solve. However, fixed stage
names and fixed failure codes can distinguish a local declaration error from
materialization, public-shape validation, or persistence without disclosing
source or private labels.

The retained original preparation error was classified by an exact/prefix
allowlist without displaying its raw text. Its safe category is
`nonliteral_demonstration_declaration`, and the AST class is `Call`. The public
failure was `ValueError`, before `Catalog.generate` was reached. The evidence is
`blind-safe-diagnosis.json`; it binds the private error record by SHA-256 without
copying that record into return evidence. No target generator, rule, canonical
row, private label, or earlier solution was inspected, and no blind reprepare
was run.

This is not evidence of a Racket mismatch. Environment-only retry cannot repair
this declaration failure. `_demonstration_count` uses `ast.literal_eval` and the
runtime's `demonstration_policy` also requires a literal declaration. The latter
normalizes a nonliteral evaluation error to a fixed message. Public `prepare`
has no demonstration-count option, and explicit `generate(..., n_train=...)`
still validates the declaration before honoring the requested count. An in-memory
policy override would broaden a validation contract. It was considered and
rejected; the original finished blocked blind record remains authoritative.

## Proposal

`prepare-reporting.patch` changes generic `src/arcpuzzles/review_solve.py` only:

- Track four fixed stages: `demonstration_contract`, `episode_materialization`,
  `public_validation`, `artifact_persistence`.
- Add a corresponding fixed `failure_code` to blocked summaries and preserved
  prepare-failure records.
- Add both scalar fields to the existing public CLI allowlist.
- Keep raw exception details private, existing status/type strings, declaration
  requirements, random seed, generation policy, and solve lifecycle intact.

The patch is a passive shared-tool proposal inside this task workspace. No shared
source was modified. `prepare_diagnostics.instrument_source` constructs exactly
the source change tested, and refuses drift if its anchors do not match exactly.
The optional patch was applied in an isolated generic-source Git tree, compiled,
and compared byte-for-byte with the tested proposal. See
`patch-verification.json`.

## Verification

From the outer packet root, the final synthetic-only regression command was:

```sh
WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python -m pytest -q generators/45922a9666b2/tests/test_prepare_diagnostics.py --tb=short --junitxml=generators/45922a9666b2/workspace/diagnostics/final.junit.xml
```

Result: **6 passed**, exit 0. These exercise the real generic preparation function
on synthetic packet fixtures; they never materialize a live task. The cases
verify stage/code visibility, private worker-detail suppression, and safe
classification of known/unknown stored errors. Mock Catalog is used only to
avoid real generation and inject a private-error sentinel at the component
boundary. No private scoring or query correctness claim follows from these tests.

The same first two assertions failed against the unmodified source with
`PREPARE_DIAGNOSTICS_BASELINE=1`, as expected: **2 failed**, missing stage/code.
`baseline.junit.xml` retains the real failure evidence. The final source bound by
`patch-verification.json` has SHA-256
`d297328c0e5ad520cd11497148c4ef1a0ce5a7cb5847d60d6dded85329f14357`.

An earlier intermediate bounded-expression-count experiment had 17 synthetic
cases passing, then an extension run displayed five expected failures and was
interrupted (exit 130). That workaround was abandoned when the literal-only
contract was confirmed. Its interpreter and tests were removed; its passing
intermediate JUnit is retained as `proposal.junit.xml` solely as intermediate
history, and is not the final proposal's test count. Default runtime Python also
lacked pytest; the packet's existing `.venv` supplied pytest successfully. An
independent process-list command during the interrupted run failed with
`fatal library error, lookup self`; it did not establish a task defect.

## Reusable safe classifier

From the outer packet root:

```sh
WORK/.venv/bin/python WORK/repo/generators/45922a9666b2/workspace/diagnostics/run_diagnostic.py classify --error-record WORK/.review/solve-private-blind/generation-error-0001.json --out /absolute/path/new-safe-diagnosis.json
```

The tool emits only fixed categories, allowlisted AST node classes, the record
path and its hash. Unknown messages remain `private_detail_suppressed`; raw
messages and memory addresses never appear in output. Output paths must be new.
No solver source, labels, or generator code are executed.

To regenerate or verify the passive shared proposal, use `run_diagnostic.py
patch --generic-source .../src/arcpuzzles/review_solve.py --out NEW.patch` and
`verify_patch.py --generic-source .../src/arcpuzzles/review_solve.py --patch
NEW.patch --out NEW.json`. `verify_patch.py` applies only to a temporary generic
source copy, then checks exact resulting bytes and compilation.

## If maintainers later authorize retry

Do not reroll the assignment or change the untouched blind target. First preserve
all original `solve-blind/` files, including FINISHED_NOTES and failure reports,
with path/size/SHA mapping under a distinct prior-solve evidence directory.
Preserve its private failure records separately within `.review`, without
publishing their raw content. A fresh lane must be prepared only after an
explicit decision about the literal-only declaration contract, retaining the
original blocker and exposure chronology. Reusing the present lane's
FINISHED_NOTES path would make a second finish fail its exclusive creation
check. No such retry or lane move has been attempted here.
