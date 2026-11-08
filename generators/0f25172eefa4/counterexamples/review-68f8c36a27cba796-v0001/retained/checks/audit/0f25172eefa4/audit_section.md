## 0f25172eefa4

**Reproduced teaching ambiguity in a default generated lesson.** Code 4 can
remain confounded with diagonal reflection after all three demonstrations, while
the query requires the intended 180-degree rotation. The existing seven-rival
lesson hook returns `[]`, and public generation records
`lesson_check.status = "passed_declared_hook"` for this lesson.

Audited source SHA-256:
`3d8e048c0a4dae89a8831c3e6a4b8cb4852b1625c61a366d59e252ab99d2f04f`
(version `2.2.0`); canonical rule hash `44e21d5003cc`. I used the current notes and
existing `review-127df307b670c69c:v0001` no-issue audit as leads, then remeasured
the current source with an additional rival. This finding does not invalidate
the prior report's explicitly bounded seven-rival measurements.

**Exact production recipe:** seed `1`, difficulty `easy`, sample-index start `2`,
three demonstrations, one query, and overrides `{}`. Public generation accepted
indices `[2,3,4,5]`, attempted four pairs, and recorded no rejections.

| Role | Sample index | Body | Ordered codes |
|---|---:|---|---|
| Demonstration 1 | 2 | `stair5`, cyan 8 | `2-3-3-4` |
| Demonstration 2 | 3 | `stair5`, yellow 4 | `4-4-5-3` |
| Demonstration 3 | 4 | `stair5`, orange 7 | `2-3-4-4` |
| Query | 5 | `l4`, maroon 9 | `3-5-4-4` |

The rival maps code 4 to matrix transpose (reflection across the main diagonal),
leaving codes 2/5, clockwise code 3, duplicate preservation, vertical centering,
and one-column gaps unchanged. The `stair5` mask's transpose equals its
180-degree rotation, so this rival reproduces all three actual Racket
demonstration outputs exactly. The L-shaped query separates the operations:
the canonical output is **3×12**, while the rival output is **3×14**.

**Domain and confirmation:** all four inputs were produced by the audited
source's ordinary default generator. Each passes `self_check` and the supported
`apply --check-generator-domain` check. Every Racket output is valid, and all
four `apply` outputs exactly match the independently materialized public episode.
The seven currently declared rivals are each refuted by at least one of these
three demonstrations; the new transpose rival is omitted from that inventory.
This is a concrete in-distribution lesson ambiguity, not a label error, rejected
custom input, or claim that the rival fits every original canonical pair.

**Suggested follow-up:** add code-4-as-transpose to the lesson competitors and
ensure a distinguishing body appears in the demonstrations. If promising safety
under every one-pair query rotation, include two independently distinguishing
pairs in each four-pair block. Consider the other standard reflection/rotation
confusions when extending the finite rival inventory. No repair is included in
this findings-only audit.

**Evidence:** retain `checks/audit/0f25172eefa4/` (nine small files). The exact input,
actual Racket query output, rival output, recipe, source/rule bindings, domain
status, command/cwd, and all demonstration evidence are in
`checks/audit/0f25172eefa4/counterexample.json`. Independent Racket results are in
`checks/audit/0f25172eefa4/racket.json`; the public episode and accepted indices
are in `checks/audit/0f25172eefa4/episode.jsonl`. Reusable probe:
`checks/audit/0f25172eefa4/probe.py`. Exact argv/cwd/exit receipts are in
`checks/audit/0f25172eefa4/commands.json`.

The Python candidate search stopped at the first witness after examining 18
raw draws: easy seeds 0 and 1, indices 0 through 8. Only the retained four-pair
lesson was confirmed through Racket; no population rate is claimed. I did not
rerun a full battery, task-test suite, or strict semantic stage because those
existing finite-rival checks do not address this new concrete rival. The
selected generator, rule, notes, shared code, and catalog were not modified.
