# Review — assignment `review-048770a49fff4022`

Both assigned homes now contain complete native parametric candidates and retained source-bound evidence.
`9c3781759581` preserves the exact canonical color-9 crop and adds a selector-parity crop branch.
`96d4a788da47` preserves the exact canonical all-object left slide and adds an anchor-indexed payload branch.
Each candidate uses two visible demonstrations and four controller-private sequential queries.
Each passed protected-Racket qualification at two settings and seeds 0 and 17: 32 label executions per target.
Each has a protected wrong-intermediate replay showing that changing only Step A's result changes the final grid.
Public projection produced 16 one-query views per target; query answers, private settings and future queries stayed hidden.
Both records are **reviewer-ready prototypes only**. Owner replay, integration acceptance and training admission remain pending.

## `9c3781759581`

### Defect → build

The supplied home had a useful older prototype, but it did not satisfy the current native contract or establish a real sequential dependency. The promoted family now has:

- `crop_policy=fixed_color_9`: the canonical Racket program byte-for-byte.
- `crop_policy=selector_parity`: count color-2 selector cells, derive odd/even, select marker color 5/9, then crop that selected inclusive bounding box.
- A wrong-intermediate program that reverses only the parity-to-color choice and changes the protected final crop.

### Checks actually run

- Focused native contract: 21 tests passed (`checks/9c3781759581/focused-tests.txt`).
- Complete task suite: 55 tests and 6,735 subtests passed (`checks/9c3781759581/task-tests-final/result.json`).
- Protected lesson audits at seeds 0 and 17: 24 labels replayed, matched inputs, both fixed-color rivals refuted by the minimum two demonstrations, public fields hidden, and 30×30 queries with 253/223 nonzero cells (`checks/9c3781759581/audit-seed-0.json`, `audit-seed-17.json`).
- Native qualification: four jobs, 32 protected-Racket evaluations, exact canonical program hash, four private queries per episode (`checks/9c3781759581/qualification/qualification.json`).
- Sequential witness replay: reversing the parity-derived target changes the final crop (`checks/9c3781759581/causal/final-check.json`).
- Export checks: 16 one-query public files and 24 first-turn invariance checks passed (`checks/9c3781759581/public-preview-public-check.json`, `first-turn-report.json`).

### Adversarial self-review

A separate author review found one important omission: prefix stability existed, but the repository's actual public projection helper was not exercised. A regression was watched failing (`checks/9c3781759581-public-projection-red.log`), then the audit was repaired to invoke `public_challenge_bytes`; the final tests and source-bound evidence were regenerated. No critical, important or minor findings remain in the bounded review (`checks/9c3781759581/self-review.json`).

## `96d4a788da47`

### Defect → build

The supplied home lacked a native parametric scaffold. The new family has:

- `slide_policy=all_objects_left`: the canonical program byte-for-byte.
- `slide_policy=anchor_indexed_payload`: count the unique connected color-8 anchor (1–3), use that value as a one-based selector among three row-ordered payloads, and slide only the selected payload to column 0 without changing its shape, rows or color.
- A wrong-intermediate program that rotates the selected payload index and changes the protected final grid.

### Checks actually run

- Focused native contract: 23 tests passed (`checks/96d4a788da47/focused-tests.txt`).
- Complete task suite: 72 tests passed (`checks/96d4a788da47/task-tests-final/result.json`).
- Protected lesson audits at seeds 0 and 17: 24 labels replayed, matched inputs, six concrete shortcut families refuted, all six held-out rotations identifiable, public fields hidden, and a 30×30 query with 464 occupied cells (`checks/96d4a788da47/audit-seed-0.json`, `audit-seed-17.json`).
- Native qualification: four jobs, 32 protected-Racket evaluations, exact canonical program hash, four private queries per episode (`checks/96d4a788da47/qualification/qualification.json`).
- Sequential witness replay: rotating only the anchor-derived index selects a different payload and changes the final grid (`checks/96d4a788da47/causal/final-check.json`).
- Export checks: 16 one-query public files and 24 first-turn invariance checks passed (`checks/96d4a788da47/public-preview-public-check.json`, `first-turn-report.json`).

### Adversarial self-review

The bounded separate pass found no open critical, important or minor issues (`checks/96d4a788da47/self-review.json`). This was an author self-review because no independent subagent interface was available in the execution environment.

## Source binding and limits

- `9c3781759581` manifest SHA-256: `9784a50e2f32231594c85671c6c764482d171405b9f7942f530007f0999b265e`.
- `96d4a788da47` manifest SHA-256: `dbf8586fd15af1b9bafe5acd6d6aeb5c4d65a0905df2f55a7eb2a5c375be4beb`.
- The checkout had no Git metadata, so immutable task-local manifests, qualification receipts and exact SHA-256 source bindings replace commit-range evidence.
- The adversarial checks are finite; they do not prove universal uniqueness or measured learning gain.
- No canonical authority, production generator or shared runtime was changed. These prototypes grant neither owner acceptance nor training admission.

## Owner next action

Integrate the patch, re-run native qualification and protected witness replay against the exact integrated bytes, then perform the separate owner acceptance gate for **both** targets.

## Final packaging verification

After the source manifests were frozen, the official task-test launcher was rerun into `checks/final-verification/`: `9c3781759581` again passed 55 tests plus 6,735 subtests, and `96d4a788da47` again passed 72 tests. Both protected causal witnesses were replayed again with `reviewer_replayed` status. A separate hash audit checked all 303 qualification-listed source files, both manifest receipts, both witness bindings and both causal receipt hashes with no mismatch (`checks/final-verification/source-binding.json`).
