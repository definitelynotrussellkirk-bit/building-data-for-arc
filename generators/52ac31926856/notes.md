# Working notes: 52ac31926856

## Current decision

Keep production generator `3.0.0`, canonical Racket rule hash
`155890c61ab00ef4a460914d2de683ae25a4b20761bb7adfae92fb324688857d`,
and `RULE_HASH = afd3c4e6c015` unchanged. The selected family supports a small
**proposed** episode-level `floor_acceptance` parameter under
`workspace/parametric/`: canonical `whole_section` versus alternative
`under_drop`.

The parameter changes only the containment predicate. Object roles, vertical
search order, section filling, and bottom-row fallback stay invariant. Inputs are
setting-independent and deliberately contain an off-column gap with red support
under the drop, so the existing canonical shortcut witness becomes a direct
cross-setting witness rather than an input cue.

## Evidence and remaining limits

Focused tests cover exact canonical identity/restoration, validation, distinct
lawful inputs, real Racket labels, three-demo/four-query rival checks, opaque
public projection, and evidence replay. Retained bounded evidence is under
`checks/parametric/floor-acceptance-v1/`; the staged selected-task test run
is under `checks/task-tests-floor-acceptance-v2/`.

This is not a canonical repair or approval request. Evidence covers two settings
and two consecutive seeds only; undeclared rules and broader sampling remain
unassessed. The direct repository pytest route cannot load the legacy
`scripts.canonical_profile_gate` namespace; the documented staged `task_tests`
route supplies that compatibility module and passes the unchanged tests.
