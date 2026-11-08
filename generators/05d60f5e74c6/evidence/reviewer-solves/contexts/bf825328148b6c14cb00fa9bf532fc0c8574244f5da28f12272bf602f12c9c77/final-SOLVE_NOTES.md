# Fresh visible-example solve work log

## Provenance and limits
This is a reviewer-authored development work log, not a captured independent
model conversation, token-level trace, or log-probability record. I had earlier
exposure to the task rule and generator during the preceding repair. After
`solve_episode.py prepare` I kept the generator, Racket rule, prior solution
explanations, reference implementations, and private labels closed. This solve
used only `solve/challenge.json`, my newly written Python, and visible feedback.
Prior exposure means this is not an unbiased blind-discovery experiment.

Final-generator binding: `fee35f721520c535929f77201658ac3ad0c01f7a4a89014a89c2ea8149f058e7`.
Episode seed: `1842382600`; four visible demonstrations and two masked queries.

## Observation experiment
Ran `python3 solve/visible_probe.py > solve/visible_component_probe.json` from
packet_root. The script reads visible training labels only and enumerates
same-color cardinally connected components. Observed 16 components across four
examples. All 16 match keeping distinct bounding-box corners exactly when the
component completely fills its box; irregular components leave no cells.
Demonstration 2 explicitly retains a singleton and two endpoints of a 4-cell
vertical bar. Demonstration 3 retains two diagonally touching same-color solid
components separately while deleting an irregular component of that color.
These examples distinguish color grouping, diagonal grouping, blanket deletion
of thin shapes, and keeping irregular objects unchanged.

## Revision 1
Wrote the public-only pytest fixture first. Its run against the provided
NotImplementedError stub produced four failures (`visible_tests_before.log`).
This is a test-first development check, not a failed inferred solution and not
an attempted model solve. Then implemented a standalone queue-based flood fill,
bounding-box area test, and corner painting in `solution.py`. No task-library
imports or hard-coded answers are used; the input is not mutated.

Ran `python3 -m pytest -q solve/test_visible_solution.py`: four passed
(`visible_tests_after.log`). Submitted this single actual solution revision to
the official visible-only checker. No deliberate wrong-rule check was needed.
A finite demonstration set cannot establish every possible input behavior; no
claim is made about independent masked-query correctness before maintainer intake.
