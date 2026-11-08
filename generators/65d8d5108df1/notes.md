# Current generator decision

Version 3.0.0 repairs the source-bound audit against SHA-256
`0f80331a001308baeeefc4ae02f979e6889f1533df5aaf283bf41689840748ba`.
All four advertised controls now use strict keyed draws, including when a named
difficulty would otherwise choose a narrower band.  The retained reproducer
request `grid_h=16, grid_w=20, n_templates=5, n_commands=5` is asserted across
eight seeds.

Library placement now uses distinct 3x3 slots, which guarantees exactly the
requested 2–5 connected templates for every valid dimension pair instead of
silently returning a partial library.  One-command samples are valid because the
public axis has always advertised `1..5`.

The canonical rule hash is pinned to `d178b58b9106`.  The executable rule mirror
uses the authoritative transform table: 1 identity, 2 clockwise, 3 half-turn,
4 left-right flip, 5 up-down flip, and 6 counterclockwise.  An asymmetric probe
template is commanded through codes 4, 5, and 6 on a three-slot schedule, giving
source-bound witnesses against no-transform, the former prose table, and
no-recolor rivals.  Generation now also rejects non-integer, boolean, or
negative seed/sample-index call controls instead of silently coercing them.
Task-local tests cover all canonical pairs, malformed command rows, deterministic
generation, exact cardinalities, strict call controls, and lesson
identifiability.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-dcc38d44a8195f95:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0f80331a001308baeeefc4ae02f979e6889f1533df5aaf283bf41689840748ba`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source665b7b59c70b957ce6327ca4762eea1c34ac4c7b0301377a7d9543bfd57f0860 consumes all four audited exact axes and guarantees template/command counts, with corrected transform codes and executed reference checks.15relocated tests, full override matrix, rule-smoke and semantic gate are reviewer-reported.

### Assessment or prior finding

## 65d8d5108df1

**A65-1 — reproduced exact-control contract defect; target left unchanged.**
The generator advertises exact axes `grid_h`, `grid_w`, `n_templates`, and
`n_commands`, but `generate()` samples all four directly from its difficulty RNG
and never reads those overrides. With the valid request
`grid_h=16, grid_w=20, n_templates=5, n_commands=5` at `difficulty=easy`, all
eight seeds 0–7 returned different dimensions/counts (for example seed 0
returned 9×10, two template IDs, and three commands) while `self_check` returned
no errors. The generated seed-0 input still executed successfully under canonical
Racket, so this is not an oracle crash; it is silent failure of the advertised
control contract. Evidence: `checks/audit/65d8d5108df1/reproducer.json`,
`input.json`, and `racket.json`. Selected generator SHA-256:
`0f80331a001308baeeefc4ae02f979e6889f1533df5aaf283bf41689840748ba`;
executed rule hash: `d178b58b9106`.

The same source has no pinned `RULE_HASH`, no task-local tests, and no semantic
contract. The isolated audit preset therefore failed its strict semantic gate
with `hooks=none`; see
`checks/audit/65d8d5108df1-combined/checks/65d8d5108df1_audit_semantic_gate.log`.
Its prose also gives an incomplete/misordered transform-code table, while the
canonical rule implements `1=id, 2=cw, 3=180, 4=flip-lr, 5=flip-ud, 6=ccw`.
Suggested repair: route every advertised axis through validated exact draws,
add override regressions, pin `RULE_HASH = "d178b58b9106"`, correct the code table,
and add source-bound semantic witnesses/lesson checks.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-dcc38d44a8195f95-v0001/audit_assets.json), manifest SHA-256 `d8e9382a880cc2234fae48a1c2b10e5038761d884dddf8ce16d89e614a5f96fd`.
<!-- arcpuzzles-current-audit-assessment:end -->
