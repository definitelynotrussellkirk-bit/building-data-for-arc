# Review: db63430eeffa
Assignment `review-2412dcedba78daeb`; generator 2.2.0 (`7c732860…`) → 2.2.1 (`909da269…`).
Defect → repair: malformed scalar requests and unknown/non-literal overrides now fail closed before keyed-draw coercion.
Lawful-degenerate metadata now agrees with the implemented `square_diagonal` domain.
Canonical Racket rule and rule hash `3e3bf77eb552` are unchanged; ordinary valid generation remains source-compatible.
Built a task-local, unapproved `path_mode` prototype: `both`, `diagonal_first`, `straight_first`, fixed once per episode.
Fresh staged suite: 30 tests plus 46 subtests pass; defect lint passes; override checker passes 119,700 planned draws.
Fresh real-Racket evidence: 3 episodes, 9 demos, 12 queries, 63/63 mirror matches, 6/6 declared rivals refuted.
Adversarial sweep: 256 seeds / 1,792 inputs, strict numeric/type rejection and public/private export checks, zero failures.
Ticket 1 retained a lawful `eb3171637821` shortcut witness; Ticket 2 produced a seeded three-record allocation audit and one Racket probe.
Remaining limit: the parameter family is evidence only—no production promotion, approval, catalog change, or training admission.
Assessment: routine repair plus a bounded proposed extension; maintainer replay/review is still required before promotion.

## Production repair

`generator.py` now validates `seed`, `sample_index`, `difficulty`, all override names, integer-valued axes, orientation, and texture before constructing the generation context. Literal integers are required (booleans and numeric-looking floats/strings are rejected), `sample_index` must be nonnegative, and an unknown key is rejected even when its value is `None`. The repair also exports `LAWFUL_DEGENERATE_TEXTURES` as the exact implemented degenerate set.

The canonical rule was not edited. The version bump is limited to the request-contract change, and the 119,700-draw override matrix retained zero findings across easy/medium/hard bands.

## Proposed parameter tool

`repo/generators/db63430eeffa/workspace/parametric/prototype.py` is a runnable evidence writer, not production code. It samples seven distinct inputs from a rule-independent stream, partitions them into three labeled demonstrations and four queries, executes all three exact Racket programs on all retained inputs, checks an independent Python mirror, scores the two finite rivals from demonstrations only, and writes content-addressed public challenges without hidden settings, seeds, programs, or query labels.

Primary evidence:

- `checks/db63430eeffa-final-task-tests/result.json`
- `checks/db63430eeffa-after-defect-lint/result.json`
- `checks/db63430eeffa-after-override-rerun/result.json`
- `checks/parametric/db63430eeffa-path-mode-final/report.json`
- `checks/parametric/db63430eeffa-path-mode-adversarial.json`
- `checks/final-artifact-syntax-and-json.log`

## Supplementary tickets

The adversarial-witness ticket reproduced one existing source-bound shortcut for `eb3171637821`: counting individual full divider rows/columns fits all eight canonical labels but disagrees on the retained lawful thick-divider witness; real Racket matches the intended output. This is support for the current audit, not a new safety finding.

The allocation-quality ticket used its pinned seed to sample `7147e98f8173`, `747486860e56`, and `7195f447bb20`. Their equal catalog weight (1.0) masks substantially different approval, unresolved-audit, and prototype states. The bounded proposal preserves the independent 10% evaluation focus and tests a 70/20/10 normal-authoring mix with explicit estimates and a stopping rule; it changes no policy. Its single executable probe on `703a842c8e24` produced four distinct Racket-matched queries while confirming a retained first-body-padding shortcut still fits all eight labels.

## Review limitations

The final review was an author self-review because this harness has no independent subagent dispatcher. The packet-native packager remains the authoritative scope, baseline, evidence, and archive validator. The storage study lacks `before_extract` because extraction had already occurred; the missing checkpoint was not reconstructed.
