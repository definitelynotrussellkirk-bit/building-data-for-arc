# Working notes: cf09cffb4663

## Review outcome (2026-10-03/04)

The selected baseline (`generator.py` SHA-256
`bbd81743fd54f75e12f58e7c13038eb8779dc943825677125cc763ed073194cf`)
produced only isolated five-cell pluses. An exact-component-size rival therefore
matched every retained baseline draw even though the canonical examples contain
longer intersecting lines. The baseline also accepted malformed inputs such as
`[[9]]`, exposed dead/inexact controls, lacked `RULE_HASH`, and declared no
executable semantic rivals.

Version 3.0.0 keeps the canonical Racket authority unchanged and rebuilds the
input curriculum around the local four-cardinal-neighbor predicate. It emits
one or two clean crosses with component sizes 6–13 plus a disconnected line or
T-junction decoy. The cyclic profiles `small_t`, `canonical_line`, and `mixed_t`
ensure that every three-example lesson refutes:

- `exact_five_component`;
- `large_component_only`;
- `degree_at_least_three`.

The public controls are reduced to `grid_h`, `grid_w`, and `n_crosses`; all are
validated, exact, and recoverable through `observe_overrides`. Placement uses a
finite backtracking search rather than retries that may silently underproduce.
The strict checker accepts all canonical inputs while rejecting malformed
palette, shape, connectivity, target, and decoy cases.

## Retained measurements

- Before battery: 6 green, 2 advisory, 4 failed of 12
  (`checks/before-full/`).
- Final battery: 12/12 green at generator SHA-256
  `1b1472b1f377b557b2d901c4e7976c41cfe3fbbd0d8fae40df642f992aa3f392`
  (`checks/after-full/`).
- Task-local regression suite: 127/127 passed
  (`checks/task-tests-final/`).
- Source-bound lesson census: 300/300 lessons had no surviving declared rival,
  with 1,196 unique inputs among 1,200 materialized pairs
  (`checks/lesson-census-after.json`).
- Cyclic probe: 54/54 three-demo windows refuted each of the three declared
  rivals; 63 unique inputs and balanced profile counts
  (`checks/cyclic-curriculum-probe.json`).

## Limits

The rival registry is deliberately finite; passing it is not a proof of
universal identifiability. The cyclic probe uses the Python mirror, so the
Racket-backed battery and census remain the authority checks. Generated inputs
stay close to the observed canonical grammar: blue orthogonal line structures
on a zero background, with one disconnected near-miss component.
## Current reviewer considerations

Source SHA-256: `1b1472b1f377b557b2d901c4e7976c41cfe3fbbd0d8fae40df642f992aa3f392`.

# Decisions for cf09cffb4663

## D1 — Preserve the canonical local rule

**Choice.** Keep the selected Racket authority unchanged: recolor a blue cell
only when all four immediate cardinal neighbors are blue.

**Rationale.** Canonical execution already passed, and the defect was in the
input curriculum rather than the transformation. Editing the rule would have
added authority risk without addressing the shortcut.

**Alternatives rejected.** Rephrasing the task as “find plus objects” or
requiring an isolated five-cell component. Both are narrower than the canonical
examples. Authority and parity evidence is in `checks/after-full/`.

## D2 — Replace unit pluses with variable-length crosses

**Choice.** Generate clean crosses with component sizes 6–13 and arm lengths
1–3, using one or two targets per grid.

**Rationale.** The baseline’s five-cell-only support made component size a
perfect rival on 120/120 sampled draws (`checks/baseline-exact-five-probe.json`).
Variable arms preserve the visible concept while breaking that equivalence.

**Alternatives rejected.** Merely randomizing the locations or count of unit
pluses; these increase surface diversity but leave the wrong hypothesis exact.
Arbitrarily large or bent objects were also rejected because they move away
from the canonical orthogonal-line grammar.

**Failure modes checked.** Multiple four-way centers in one component,
disconnected arm gaps, targets touching decoys, and impossible small-grid
layouts. The checker and backtracking placement cover these cases.

## D3 — Use explicit near-miss decoys

**Choice.** Add one disconnected straight line in `canonical_line` and a unit
T-junction in the other profiles.

**Rationale.** A straight line demonstrates that blue components are not
recolored merely for being elongated. A T-junction distinguishes the exact
four-neighbor predicate from “mark any branchpoint.”

**Alternatives rejected.** Singleton noise and arbitrary blobs. They provide
weak or unrelated negatives and could teach an object-counting side task.

**Limitation.** The decoy vocabulary is intentionally small; it targets the
most plausible canonical-compatible rival, not every conceivable distractor.

## D4 — Make three consecutive examples a complete curriculum

**Choice.** Cycle `small_t`, `canonical_line`, and `mixed_t` by sample index,
with difficulty-specific offsets but the same period.

**Rationale.** The production lesson uses three demonstrations. Distribution-
wide witness counts do not ensure each lesson contains the needed contrasts.
Every three consecutive starts therefore covers all profiles.

**Probe.** `workspace/curriculum_probe.py` reads the live
`LESSON_COMPETITORS` registry and checks all cyclic starts. The retained run
covers 54 windows and refutes each rival in all 54
(`checks/cyclic-curriculum-probe.json`).

**Alternative rejected.** Independent random profile sampling. It can produce
three homogeneous demonstrations even when the marginal distribution is good.

## D5 — Reduce controls to three exact, observable axes

**Choice.** Expose only `grid_h` (8–10), `grid_w` (9–11), and `n_crosses`
(1–2). Validate types/ranges before generation and reject unknown keys.

**Rationale.** The baseline advertised eight controls, many dead or incompatible
with difficulty-specific draw ranges. A small honest API is better training and
better replay metadata than nominal combinatorial breadth.

**Alternatives rejected.** Keeping aliases such as `texture`, fake palette
controls, or diagnostic degenerates in the normal override domain.

**Probe.** The final override stage exercised 32 cases across three bands and
accepted 2,880/2,880 draws with exact observations.

## D6 — Use finite backtracking rather than retry-and-drop placement

**Choice.** Precompute legal target/decoy candidates, shuffle deterministically,
and search for a non-touching combination.

**Rationale.** The old bounded random retry loop could silently produce fewer
objects than requested. The finite search makes exact counts a contract and
fails loudly only if the declared domain is impossible.

**Trade-off.** Candidate construction costs more than a few random placements.
The pools are small at the declared dimensions, and the completed override
matrix shows the runtime remains practical.

## D7 — Tighten the validator to the supported teaching grammar

**Choice.** Reject malformed dimensions, ragged rows, non-integer or non-{0,1}
palettes, absent background, wrong target counts, invalid target topology, and
invalid decoys.

**Rationale.** The baseline returned no error for `[[9]]`, so an acceptance-only
checker could not guard training inputs. The final checker also accepts all
canonical inputs, preventing overfitting to only newly generated scenes.

**Alternative rejected.** A generic “grid is rectangular and colors are 0–9”
check. It cannot certify that an input actually teaches this task.

## D8 — Declare executable rivals and canonical shortcuts

**Choice.** Register `exact_five_component`, `large_component_only`, and
`degree_at_least_three` as executable competitors; mark the latter two as
canonical shortcuts because each fits all five usable canonical pairs.

**Rationale.** Names or prose are insufficient for automated lesson scoring.
Executable functions let the semantic gate and census prove where a lesson
separates the selected rule from each rival.

**Limitation.** This is a finite registry. It establishes targeted evidence,
not universal induction uniqueness.

## D9 — Add tests before implementation and retain failures

**Choice.** Encode exact controls, validator rejection, profile coverage,
canonical support, and rival refutation as task-local tests before replacing the
generator. Add a separate test-first curriculum probe.

**Evidence.** The first generator test run failed 116 tests and passed 10
(`checks/task-tests-red.log`). The probe test first failed because the tool did
not exist (`checks/curriculum-probe-red.log`). Final source-bound task tests
passed 127/127 (`checks/task-tests-final/result.json`).

## D10 — Keep the reusable probe task-local

**Choice.** Put `curriculum_probe.py` under the selected task workspace rather
than modifying shared infrastructure.

**Rationale.** It immediately helps future reviewers while respecting the
allowed delta. `FEEDBACK_TO_CODEX.md` separately proposes promoting the concept
to the shared semantic/lesson tooling after a maintainer decision.
