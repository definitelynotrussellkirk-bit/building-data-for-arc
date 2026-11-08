# Working notes: ead22faa41ef

## Current decisions

- Canonical authority is unchanged: rule hash `6615d26334ba`, full Racket SHA-256 `fc2471b9a0fe8f3bf1318728a845cb54408e2d80744b6da6deca664a681cdbaa`.
- Production source is version `3.1.0`. The known lesson shortcut was that three demonstrations could contain no preserved lone 3/2 cells, allowing a global `3→8, 2→0` replacement rule to fit the demos but fail the query.
- The default lesson schedule now has declared period 2. Even slots contain at least one preserved lone 3 and lone 2; therefore every three-of-four rotation retains a demonstration that refutes global replacement. `LESSON_COMPETITORS` and `lesson_identifiable` make that claim executable.
- The canonical generator API and Racket rule remain fixed. The input distribution change is limited to witness-bearing default lesson slots; explicit overrides retain their prior behavior.
- A separate proposed prototype under `workspace/parametric/` adds episode-fixed `survivor_role ∈ {green3, red2}`. `green3` is the byte-exact canonical default; `red2` swaps which member of an isolated 3/2 pair survives as cyan 8. Input generation is independent of the hidden setting.
- Each prototype episode uses three labeled demonstrations and four distinct queries. Every label is executed in matching Racket; demos refute both the alternate parameter and the historical global-replacement shortcut before query answers are considered.
- Public challenge names are SHA-256 IDs of canonical visible bytes only. Hidden parameters, seeds, Racket text, and query outputs do not affect the public name.

## Retained evidence

- Source-bound task tests: `checks/ead22faa41ef-task-tests-after/result.json` — 24 tests and 14 subtests passed.
- Strict teaching check: `checks/ead22faa41ef-semantic-after-final/` — 12/12 lessons identifiable and 0/48 ambiguous query rotations at fixed seed 0.
- Prototype evidence: `checks/parametric/survivor-role/report.json` and its verifier — four canonical labels plus 14 episode labels replayed, both settings covered, zero query ambiguities.
- Adversarial probe: `checks/parametric/survivor-role-adversarial.json` — 56 independent parameter/Racket parity labels passed and a one-byte public-file tamper was rejected.

## Limits and next action

Evidence is finite (declared settings, selected seeds, and two rival families), not a uniqueness proof over arbitrary rules. The prototype is proposed only: it does not alter the shared parametric API, catalog approval, canonical authority, or training admission. The next useful action is maintainer review of the `survivor_role` semantics and, only if accepted, a separately scoped shared integration proposal.

## Prototype public emission order resolved

The task-local materializer now constructs and validates the complete two-episode batch in memory, rejects duplicate visible challenge IDs before creating the destination, and writes public challenge files in public-ID order. Private episode numbering, report order, labels, and Racket programs remain in their original seed/setting enumeration. A regression reverses that private order and observes sorted public writes; a second regression proves duplicate visible content leaves no destination. Focused evidence is under `checks/reconcile-public-order/`.

The production generator and canonical authority remain unchanged. The survivor-role prototype is still proposed and unapproved; the two inherited same-source teaching audits remain explicitly indexed against their audited pre-3.1.0 source, and this writer-only change does not clear them.
