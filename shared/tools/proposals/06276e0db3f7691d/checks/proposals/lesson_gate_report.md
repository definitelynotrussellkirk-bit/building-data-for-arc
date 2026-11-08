# Optional production lesson-rival gate proposal

**Optional only; not applied to the selected repair or repository.** The unified
patch changes only `src/arcpuzzles/worker.py` when an owner elects to apply it.

## Root cause and proposed behavior

Production `lesson_check` currently reads only `lesson_identifiable` and the
resolved demonstration minimum. Declaring `LESSON_COMPETITORS` or
`CANONICAL_SHORTCUTS` alone therefore produces `not_declared`; even a rival that
fits every demonstration and disagrees with the materialized query does not
reject automatic generation. Authoring census/semantic tools checking these
attributes do not change that production behavior.

The patch evaluates both named declarations against the **actual materialized
inputs and reference labels**, without new generation or authority calls. A
rival is `ambiguous` only if it fits every demonstration and disagrees with a
labeled query. A rival refuted by any demonstration is `refuted` and needs no
query evaluation. A survivor agreeing with every query is `survived_all` and is
accepted. All materialized queries are checked for demo survivors.

Invalid declarations, callable exceptions, malformed predictions, observed input
mutation and inconsistent consecutive predictions become explicit diagnostic
reasons. The existing automatic policy raises on unsupported lessons; explicit
requests receive diagnostics. Existing hook execution, hook purity checks,
minimum handling and `passed_declared_hook` status remain intact. Rival-only
passes use `passed_declared_rivals`; additive `contract`, `rival_declarations` and
named `rivals` fields distinguish hook-only, rival-only and combined evidence.
Empty dictionaries provide no executable rival contract. `SEMANTIC_RIVALS`
remains outside this lesson-specific production contract.

The existing portable `reviewer_support.normalize_grid` helper is reused. Its
runtime mapping already installs it as `reviewer_support.py`; no mapping or
catalog update is proposed. Existing rival scorers were examined: they include
additional semantic declarations and do not detect mutation, so their broader
scoring internals were not copied into the production worker.

## Regression evidence

Run from the packet root (`arc_review`):

```bash
python3 WORK/checks/proposals/lesson_gate_regression.py --mode original > WORK/checks/proposals/lesson_gate_original.txt 2>&1
python3 WORK/checks/proposals/lesson_gate_regression.py --mode patched > WORK/checks/proposals/lesson_gate_patched.txt 2>&1
```

| Worker | Tests run | Recorded result | Exit |
|---|---:|---|---:|
| Original | 19 | Expected red: 13 assertion failures and 4 missing-field errors, including declaration subtests | 1 |
| Patched temporary copy | 19 | All passed; 0 failures, 0 errors | 0 |

The original missing-field errors are regression assertions against absent new
provenance fields, not production exceptions. Decisive original failures include
both automatic-rejection tests and explicit ambiguity diagnostics. The same
suite also checks agreement acceptance, refutation by the second demo, every
query, bad declarations, mutation, exceptions, malformed predictions, the
consecutive-call consistency probe, hooks and demonstration-minimum policy.
All fixtures are tiny literal grids. No canonical pairs, draws or private solves
are used. Tests apply the patch to a `TemporaryDirectory` worker copy and verify
the original worker bytes afterward.

`lesson_gate_source_hashes.json` is a compact source receipt: 51,417 original
files were inventoried, and 51,404 protected files were compared after excluding
the separately authorized selected-task namespace and ephemeral pytest cache.
The before/after aggregate hashes match; the changed-path list is empty.
Worker and reused helper hashes match their originals. No repository, shared,
root-test or catalog file was edited by this proposal. The full inventory was
compacted away. The source snapshot has no Git metadata, so a Git status check
was unavailable; byte comparison supplies the source-preservation evidence.

## Limits and owner review considerations

- This checks declared rivals on one materialized lesson. An accepted result
  does not prove universal identifiability or completeness of the rival set.
- Rivals must be pure and deterministic. Two calls on independent input copies
  detect immediate observable mutation and some inconsistent predictions. They
  cannot prove purity or determinism, detect mutate-and-restore behavior, or
  isolate module/global/external side effects. Execution remains under the
  existing worker timeout; no per-rival timeout is added.
- Using the existing normalization helper intentionally permits digit-string
  rows as well as integer-list grids, and normalizes both to integer-list
  predictions. This follows the authoring census convention. It is not an
  exact integer-list-only return contract; an owner wanting that stricter API
  should reject strings before normalization and add its own regression.
- Scoring stops for a rival when a demo refutes it. Later inputs are not purity
  or exception probes for that irrelevant rival. Every evaluated failure is
  reported; irrelevant query behavior does not manufacture an ambiguity.
- At most two calls occur per evaluated pair per rival. Large rival sets increase
  production cost. No bounded rival-count policy is added.
- New rival-only statuses and additive provenance fields are an optional public
  output change. Existing hook pass status is preserved. No packaging, dataset
  export, Racket run or whole-repository battery was needed or exercised here.
