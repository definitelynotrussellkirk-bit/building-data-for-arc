Task: `36275402c6b2`, generator version `4.1.0`, assignment `review-6679827af5566d57`.
Defect: the issued public API accepted or coerced malformed scalar arguments; baseline `defect_lint` reported 123 `strict-scalar` warnings.
Repair: add a task-local boundary validator for seed, sample index, difficulty, and all six declared integer overrides; legal generation is unchanged.
Final generator SHA-256: `14022562017859a64a23690f41a578166a72b2f153bdecb5b71e0e56c3ffd2a0`.
Reference rule: unchanged; canonical Racket bytes and normalized `RULE_HASH` `08894540e7f2` were not edited.
Checks: after battery 12/12 green; local and fresh-replay portable task tests 70/70 green; 100/100 sampled valid calls byte-identical to the issued generator.
Lessons: production uses three consecutive accepted demonstrations plus one query; 300/300 lessons and 1,200 inputs materialized with 0 production ambiguities and 0/1,200 query-rotation ambiguities against six distinct declared rivals.
Parametric assessment: proposed `border_policy={recolor,preserve}` prototype; four Racket-backed three-demo/one-query episodes distinguish the nonselected setting in every demonstration and query.
Post-repair solve: first Python revision passed all three visible examples; earlier rule exposure is disclosed and no reference was consulted during the solve.
Remaining blocker: none for the selected repair; finite rival checks are not a proof against every possible shortcut, and the proposed parameter is not production-approved.
Acceptance: routine.

# Review details

## Defect, root cause, and repair

The before battery is retained at `checks/before/result.json`. Eleven of twelve
stages were green; `defect_lint` alone failed because the legacy draw context
accepted or converted malformed values at the public `generate(...)` boundary.
Examples included boolean seeds, negative sample indices, numeric difficulties,
and float or string values for declared integer axes. The detector produced 123
warnings; `pair_count=3.75` is one concrete baseline case.

The production patch validates the call before constructing `GenCtx`:

- `seed` and `sample_index` must be non-negative literal integers, excluding booleans;
- `difficulty` must be `None`, `easy`, `medium`, or `hard`;
- `grid_h`, `grid_w`, `rect_h`, `rect_w`, `pair_count`, and `frame_color` must be
  literal integers when supplied; `None` remains the shared no-override sentinel;
- unknown override names are still rejected first by the existing contract.

This is deliberately task-local. It fixes the selected generator without changing
shared runtime semantics for thousands of other tasks. The source-paired probe
`checks/valid-output-parity.json` regenerated 100 valid calls through both the
issued and repaired modules and found all 100 outputs byte-identical. Representative
accepted-before/rejected-after calls are retained in
`repo/generators/36275402c6b2/counterexamples/strict-scalar-calls.json`.

## Verification

| Evidence | Result |
| --- | --- |
| `checks/tdd-red-strict/result.json` | Regression matrix failed before the validator: 33 failed, 29 passed. |
| `checks/tdd-green-strict/result.json` | Same matrix passed after the validator: 62/62. |
| `checks/defect-lint-after-scalar/result.json` | Dedicated defect-lint stage green. |
| `checks/task-tests-final/result.json` | Final portable selected-task snapshot: 70 passed, 0 failed/errors/skipped. |
| `checks/after/result.json` | Full after battery: 12 green, 0 advisory, 0 failed. |
| `checks/after/attempts/0001/result.json` | Honest first after attempt: controller SIGTERM after 3 green stages; 9 remained pending. |
| `checks/lesson-census.summary.json` | 300 lessons, 1,200 pairs and unique inputs; zero production or rotation ambiguity. |
| `checks/valid-output-parity.json` | 100/100 valid calls identical before/after. |
| `checks/final-replay-candidate/replay.json` | Source patch applied to all seven paths in a fresh full 94,130-file extraction; final generator hash matched. |
| `checks/final-replay-candidate/task-tests/result.json` | Fresh replay checkout portable task tests: 70/70 green. |

The candidate return was replayed onto a fresh full extraction before the final
package. All seven changed paths matched the current worktree, the replayed
generator SHA-256 was `14022562017859a64a23690f41a578166a72b2f153bdecb5b71e0e56c3ffd2a0`,
and its portable task tests passed 70/70. The final package adds only these replay
receipts and handoff metadata; the source patch is unchanged.

The first after-battery controller was externally interrupted and is preserved
rather than presented as a pass. The unchanged-source `--resume` completed all
remaining stages; `checks/after/result.json` records `resumed: true` and the final
12/12-green verdict.

## Lesson and distribution evidence

The existing lesson contract was not changed. Each lesson consists of three
consecutive accepted examples in production order and the next accepted draw as
its query. The larger Racket-labelled census used 100 lessons in each of easy,
medium, and hard. It materialized all 300 requested lessons, 1,200 labelled pairs,
and 1,200 exact unique inputs with no materialization or scoring errors. The six
unique rivals are declared through both `LESSON_COMPETITORS` and
`SEMANTIC_RIVALS`; every production lesson refuted them. Holding out each of the
four labelled pairs in turn while preserving the remaining order yielded 1,200
query rotations and zero ambiguities. The full report is
`checks/lesson-census.json`; the intake-sized result is
`checks/lesson-census.summary.json`.

These are finite checks of the current sampler and rival set. They do not certify
arbitrary export-time shuffling, every possible hypothesis, or downstream model
accuracy.

## Parametric-rule assessment

A suitable one-parameter extension is implemented as a **proposed prototype**, not
as a production rule change:

- source: `repo/generators/36275402c6b2/workspace/parametric/prototype.py`;
- parameter: `border_policy` with values `recolor` and `preserve`;
- canonical/default setting: `recolor`;
- `recolor` Racket SHA-256:
  `a806f83cdfb3f7831cfe4c189fee46cdc90677706f05b67cb617dafc2b080f86`;
- `preserve` Racket SHA-256:
  `5a8d1921b25645b4ea5184c59385e02bff66d4ae00d1709d3ced24c77eb4c48e`.

Both settings preserve the original largest-component crop and exterior
`(replacement, source)` legend roles. Only mapped source cells on the crop border
change policy. Seeds 0–3 produced four complete, Racket-executed episodes,
alternating both settings. Each episode has three demonstrations and one query;
all three demonstrations and the query distinguish the opposite setting. The
source-bound evidence and runtime identity are in
`checks/parametric/border-policy/manifest.json`. The default program is the exact
canonical program. The evidence is intentionally bounded to four seeds and the
odd border-witness profile.

## Visible-only solve records

The mandatory pre-repair blind solve is finished under `solve-blind/`, bound to
untouched task `5a8d42591332`; one revision passed all three visible examples,
with no earlier rule exposure or reference consultation. The post-repair solve is
finished under `solve/`, bound to the final selected-generator SHA-256 above. Its
first revision also passed all three visible examples; earlier exposure is marked
`yes`, and reference consultation during the solve is marked `no`.

## Adversarial audits

The audit lane did not modify either target.

| Target | Finding | Reproducer |
| --- | --- | --- |
| `ead22faa41ef` | Seed 3351, medium, indices 0–2 teach the shortcut “replace every 3 and 2 globally”; index 3 contains three lone 2s and refutes it. | `checks/audit/ead22faa41ef/counterexample.json` |
| `0cb23f5660c9` | Seed 2127, easy, indices 0–2 make 90° rotation invisible; the index-3 vertical bar distinguishes the no-rotation crop shortcut. | `checks/audit/0cb23f5660c9/counterexample.json` |

The first target's optional portable task-test preflight failed on a fixed
`parents[...]` path (exit 2), and the second reported no task-local/frozen tests
(exit 5). Those limitations are retained in the audit evidence and are separate
from the independent generated-input plus canonical-Racket reproductions. Full
findings and suggested repairs are in `AUDIT.md`.

## Self-review

The selected repair introduces no new grid pattern, lesson ordering, palette, or
geometry restriction; it rejects malformed call values before the pre-existing
sampler runs, and the 100-call paired probe found no valid-output change. A new
shortcut therefore cannot arise from the repair's data distribution, but the
finite six-rival census cannot exclude undeclared hypotheses, and the parametric
prototype remains separate from canonical training admission.
