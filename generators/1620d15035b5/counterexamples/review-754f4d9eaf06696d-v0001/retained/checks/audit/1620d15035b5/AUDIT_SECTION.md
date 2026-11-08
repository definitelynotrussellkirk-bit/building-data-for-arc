## 1620d15035b5

**A1620-1 — Suspected shortcut, concretely reproduced: legend endpoints replace counting on the generated distribution.** Audit-only finding; no generator, rule, catalog, assignment, or task-owned files changed.

Audited version `2.1.1`, generator SHA-256 `87816283b6d463c327a8315a97819548d2427fa1b3efe15afd31329a42fe9fbc`. Selected Racket rule hash `ff5967e7954e`; executed rule-text SHA-256 `e5d30ac3575cc149b64275a58ed9559db5db6a667a1710dcb61188df99c3d78c`. The public apply receipt confirms the executed rule matches the catalog. Current `notes.md` contains only its starter text; `evidence/associated_notes.jsonl` is empty, and no target `review_index.json` or task-local tests directory exists.

`generator.py` lines 157–161 always paint area marks at columns `1..K` and width marks at rows `1..W`. Consequently the last marked coordinate equals the legend's count. The retained rival reads the rightmost color-1 column and bottommost color-3 row as the two requested features, then selects an object with those features. It never counts legend marks. This is a distribution/teaching concern: the audited generated labels were correct; the issue is that those inputs cannot distinguish the intended count rule from this rival.

### Concrete separating example and domain

The authored input is **10 rows × 12 columns**. Its reference output and rival output are each **10 rows × 12 columns**. All coordinates below are zero-based.

| Feature | True count | Endpoint rival |
|---|---:|---:|
| Color-1 top-row marks at columns 1, 2, 3, 5 | Area 4 | Area 5 |
| Color-3 left-column marks at rows 1, 3 | Width 2 | Width 3 |

The true target is a four-cell square at `(4,3), (4,4), (5,3), (5,4)`. The distractor has five cells and width three at `(6,7), (6,8), (6,9), (7,8), (8,8)`. **Actual Racket output retains the square in color 8; the rival retains the distractor in color 8.** Both outputs are retained in [checks/audit/1620d15035b5/counterexample.json](checks/audit/1620d15035b5/counterexample.json), alongside the exact input, source/rule identities, public command, and provenance.

This is an **authored counterexample**, not a claimed generated draw: seed, sample index, difficulty and overrides are explicitly `null`. `self_check` accepts it with `[]`; public `apply --check-generator-domain` independently records `valid` with no errors. It satisfies the documented generator domain: legal colors, positive legends within their declared ranges, two interior objects, and exactly one object matching both legend counts. It is outside the current ordinary generator's placement support because its legends contain gaps. Sparse top-row legends are also present in all three retained labeled canonical pairs. The endpoint rival fails those three pairs; it is **not** claimed to be a canonical-fitting shortcut.

### Bounded checks and limits

- **96/96 unique generated inputs** from seed `0`, sample indices `0..31`, each of `easy`, `medium`, and `hard`, with `{}` overrides, pass `self_check` and the probe's explicit documented-domain checks. All 96 have endpoint values equal to counts; the endpoint rival agrees with the Python count-rule probe on 96/96. These 96 comparisons are Python/source observations, not 96 Racket executions.
- **9/9 generated reference checks**, seed `0`, indices `0,15,31` in each band, agree between the rival, the count-rule probe and fresh public Racket outputs. **1/1 authored reference check** separates the rival from Racket. Racket returned outputs without errors and recorded valid generator-domain checks for all **10/10** inputs.
- The count-rule probe matches **3/3** retained canonical labels, and the endpoint rival matches **0/3**. Canonical comparisons use `reviewer_support.canonical_pairs`; newly executed reference outputs are separately retained in [checks/audit/1620d15035b5/racket.json](checks/audit/1620d15035b5/racket.json).
- No task-test stage or full battery was run: there are no target task tests, and the bounded reference batch resolves the stated finding. No lesson-identifiability verdict, universal generated-output correctness claim, or training approval is inferred. No `CANONICAL_SHORTCUTS` or `LESSON_COMPETITORS` declarations exist to iterate.

Recommended task-local follow-up: vary the legal positions and gaps in each legend and include witnesses where endpoint coordinates imply a different existing candidate. Verify complete lessons against this rival. This is a proposed follow-up, not an implemented patch.

Reproduction and complete measured scope: [checks/audit/1620d15035b5/probe.py](checks/audit/1620d15035b5/probe.py), [checks/audit/1620d15035b5/probe.json](checks/audit/1620d15035b5/probe.json), [checks/audit/1620d15035b5/input.json](checks/audit/1620d15035b5/input.json), [checks/audit/1620d15035b5/rival_outputs.json](checks/audit/1620d15035b5/rival_outputs.json), and [checks/audit/1620d15035b5/COMMANDS.json](checks/audit/1620d15035b5/COMMANDS.json). All three verification commands exited `0`; logs are retained beside the evidence. The generator hash above binds every reported count; no source edits occurred during this audit.
