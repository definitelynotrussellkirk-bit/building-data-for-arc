## 109e6056a258

**A2 — Reproduced exact-control defect; existing finding independently confirmed.**
The selected `repo/generators/109e6056a258/generator.py` is unchanged at
SHA-256 `7688ff7c305cda205d115c5bf6aeb9f247d7d66e412956a6b224c4d4e3285046`.
Its advertised exact `op_key` and `tf_key` axes are ignored: `generate()` samples
both keys directly from its layout RNG. This confirms the already unresolved
`review-78fdee0a9f8452e7:v0001` finding in the target's current review index;
it is not presented as a newly discovered defect.

**Minimal reproduction.** With seed `audit-op-tf-exact-controls`, sample index
`0`, difficulty `medium`, requests `{op_key: 1, tf_key: 1}` and
`{op_key: 5, tf_key: 6}` produce byte-identical 10×12 grids containing keys
`(5,1)`. Both requests therefore miss their advertised key setting (2/2),
while both outputs pass `self_check` (2/2 calls; one unique generated input).
The paired-input equality result is 1/1, not a new 100-sample census.

The supported canonical Racket execution demonstrates that these ignored
controls change the requested semantics on the same geometry:

| Case | Corner keys | Actual Racket output |
|---|---|---|
| Generated input for either request | `(5,1)` | `[[3,0],[0,0],[0,0]]` |
| Same input with first requested keys | `(1,1)` | `[[3,8],[0,8],[2,2]]` |
| Same input with second requested keys | `(5,6)` | `[[3,0],[3,0],[0,0]]` |

All 3/3 Racket outputs are valid, and all three inputs pass the target validator.
The two counterfactuals change only legal corner keys, retaining the generated
sizes, component shapes, distinct colors, separation and positions; they lie
within the documented input domain. The counterfactual outputs are the explicit
rival “honour the requested keys on this geometry,” not claims about a future
repair's complete RNG layout. Selected canonical rule hash: `28677d40f4a8`;
executed rule-text SHA-256:
`329ed1a947e55f01cf1e9da4bc014596fe12073ba51620c00f4ecf2280709c8f`.

**Evidence and reproduction.**
`checks/audit/109e6056a258/probe.py` generates the witness with `prepare` and
checks the reference receipt with `summarize`.
`checks/audit/109e6056a258/input.json` contains the three exact input grids;
`checks/audit/109e6056a258/racket.json` is the supported `arcpuzzles apply`
receipt with outputs, hashes and command;
`checks/audit/109e6056a258/audit_record.json` contains requested/observed values,
source hashes, validator results, the rival definition and source-bound conclusion.
Exact successful argv/cwd records are in
`checks/audit/109e6056a258/commands.json`.

**Scope and disposition.** Inspected the selected source, current notes and review
index, the one canonical row (four public authoring pairs), and Racket component
semantics. The candidate connectivity discrepancy was ruled out: both the
Racket `objects` primitive and `self_check` use same-color 4-connected components.
There are no target-local tests in the packet; no blanket battery, lesson census,
shortcut census, or new all-branch correctness claim was made. This is one fixed
seed/index witness plus two legal interventions, bound to the unchanged final
source above. No additional semantic defect was established in that scope.
Keep the existing finding unresolved until the exact controls are implemented
and tested. The target generator, its Racket authority, and shared internals
were not edited.
