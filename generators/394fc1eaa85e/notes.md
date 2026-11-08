# Working notes: 394fc1eaa85e

## Rule and unchanged authority

The canonical rule remains unchanged (`RULE_HASH = bc441550caa9`). Treat color 5
as impassable walls. Starting from the unique red 2 and green 3 cells, compute
4-neighbor shortest-path distances through every non-5 cell. Recolor an open 0
cell cyan 8 only when both distances are finite and equal; preserve all other
cells. The Python mirror already matched the canonical examples and Racket, so
this review changed the curriculum rather than the authority.

## Reproduced curriculum defect

The retained lead `review-088fbb6f91283037:v0001` identified a real teaching
hole: generated scenes had no open cell unreachable from both seeds. The wrong
solver `unreachable_as_tie` uses ordinary Python equality on missing distances,
so `None == None` turns a doubly unreachable 0 into cyan. It fit the old synthetic
lessons even though a lawful canonical pair refuted it. The baseline 12-stage
battery was green, demonstrating that label correctness alone did not cover this
undefined-distance semantic branch.

## Repair

Version 2.3.1 adds the rival and a matching semantic witness. The original frozen
four-profile schedule remains exactly:

1. `none`
2. `vertical_gate`
3. `horizontal_gate`
4. `elbow_gate`

Horizontal and elbow scenes each embed a disjoint closed 3x3 wall ring around one
open center. Candidate construction is accepted only when that center is the
**only** open cell unreachable from the seeds; this prevents the auxiliary ring
from accidentally combining with a gate to cut off a larger region. The ring is
removed only for primary-profile classification, so the observable schedule and
existing frozen fixture remain intact.

With three demonstrations and one query, every three-pair window contains at
least one finite-reachability witness. Every four-pair lesson contains two such
witnesses, so holding out any one pair as the query still leaves one in the
three demonstrations. All declared rivals are evaluated from the generator's
own `LESSON_COMPETITORS` registry.

## Tests and evidence

Final generator SHA-256:
`784de331e6043d6f980c7057e0d814faed0d1ee6b0bad748e893d476b6cb2504`.
The baseline test fixture remains byte-identical at
`021a6284ee5067e7afa0b778d55c8ea9a525f069766199f22b6db6cc7df35a40`.
New coverage lives in `tests/test_unreachable_curriculum.py` and checks:

- the declared missing-distance rival;
- every cyclic three-demo window in every difficulty band;
- every query rotation over each four-pair schedule phase;
- exact one-cell isolation for targeted seeds that previously exposed accidental
  large disconnected components.

`checks/semantic-probe-final/report.json` sampled 288 generated inputs (8 seeds ×
12 indices × 3 bands), 96 overlapping production windows, and 384 query
rotations. It found zero failures; all 144 island-bearing inputs had exactly one
unreachable open cell. `checks/lesson-census.json` independently materialized
300 lessons (100 per band), 1,200 labelled pairs / 1,194 unique inputs, and 1,200
query rotations with zero declared-rival ambiguity in either production or
rotated roles.

## Rejected alternatives and limits

Adding a fifth `island` schedule profile would have broken the frozen four-profile
contract. Placing only one island per longer cycle passed ordered production but
failed query rotation when the lone witness became the query. Accepting any
nonzero unreachable count also produced scenes where the ring and gate jointly
isolated 4–35 open cells; exact one-cell acceptance was adopted instead.

The evidence is finite and only excludes declared rivals. It is not a proof of
unique induction over all possible programs, and it does not establish downstream
Qwen3.5-9B accuracy. The retained task fixture still imports the legacy
`scripts.canonical_profile_gate` namespace; the supported task-test wrapper emits
an advisory warning, but the fixture was deliberately left unchanged.
## Current reviewer considerations

Source SHA-256: `784de331e6043d6f980c7057e0d814faed0d1ee6b0bad748e893d476b6cb2504`.

# Decisions — 394fc1eaa85e

## R1 — Fix the curriculum, not the authority

The Python mirror and canonical Racket rule agreed on the five usable canonical
pairs, and `RULE_HASH = bc441550caa9` remained synchronized. The reproduced
failure was that generated lessons did not exercise the rule's finite-distance
precondition. Changing Racket would have changed correct semantics, so the repair
is limited to generator curriculum, declarations, and tests.

## R2 — Model the exact missing-distance shortcut

I added `unreachable_as_tie` as a pure declared rival. It computes two BFS maps
but compares `dict.get` results directly; two absent values therefore compare
equal and wrongly paint a doubly unreachable 0. This is more diagnostic than a
generic random rival because it corresponds to the concrete canonical-versus-
synthetic support gap from retained lead `review-088fbb6f91283037:v0001`.

## R3 — Preserve the frozen four-profile contract

A fifth standalone island profile was rejected because the packet's baseline test
fixes the schedule to `none`, `vertical_gate`, `horizontal_gate`, `elbow_gate`.
Instead, one closed 3×3 ring is embedded in each horizontal and elbow scene. The
ring is removed only when classifying the primary wall topology, so generated
grids still expose the original four-profile cycle while adding two independent
finite-reachability witnesses per four-pair lesson.

## R4 — Require two witnesses for query-role robustness

One island per four pairs passed the ordered 3-demo-plus-query export, but a
source-bound 100-per-band census found 176/1,200 ambiguous query rotations when
the only island became the query. Alternating two witness-bearing profiles means
any one held-out pair leaves at least one witness among the three demonstrations.
The final strict rotation gate, exhaustive schedule-phase tests, 384-rotation
probe, and 1,200-rotation census all pass.

## R5 — Isolate exactly one open cell

A disjoint ring can still combine with a long gate to disconnect a larger region.
A regression reproduced 32, 4, and 13 unreachable cells for three pinned cases.
The constructor now retries unless the expected unreachable count is exactly one
for horizontal/elbow profiles and exactly zero otherwise. This keeps the negative
minimal and prevents a new shortcut based on bulk disconnected area.

## R6 — Keep the frozen fixture frozen

An intermediate edit adapted the baseline fixture to a changed schedule. That was
reversed: `test_generator_394fc1eaa85e.py` is byte-identical to the packet
baseline. New behavior is tested only in the new task-local file. The final patch
replay receipt independently confirms the frozen SHA and 31 passing cases.

## R7 — Evidence and stopping rule

I stopped after the final source passed the 12-stage battery, strict rotation
semantic gate, 31 task tests, the broad exact-isolation probe, the 300-lesson
census, a fresh visible-only solve, and a clean fresh-packet patch replay. The
remaining epistemic limit is undeclared hypotheses: zero survivors among declared
rivals is not a proof that no possible shortcut exists.

## A1 / A2 — Audit targets are findings-only

For `3ef9eae12446` and `f869ac2ae3e4`, I retained minimal reproducible probes and
canonical Racket outputs but made no source changes, as required by the lane
assignment. Their findings are described separately in `AUDIT.md`.
