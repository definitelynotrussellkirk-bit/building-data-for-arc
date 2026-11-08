# Working notes: 9a1459fe40d0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ca0769ff471fd93a:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `55f725bfacf1db458e29cb59c5b3e3cf30367a9a7f8e339c280aad2e9ca52356`. At disposition, audited bytes match the current source.

### Current decision

Audited source repo/generators/9a1459fe40d0/generator.py SHA256 55f725bfacf1db458e29cb59c5b3e3cf30367a9a7f8e339c280aad2e9ca52356. Bounded no_issue against tested declared rivals only; legacy import warning retained. No owner execution or peer repair. Exact evidence: `checks/audit/.9a1459fe40d0-combined-current.check.lock` `checks/audit/9a1459fe40d0-combined-current.driver.rc` `checks/audit/9a1459fe40d0-combined-current.driver.stderr` `checks/audit/9a1459fe40d0-combined-current.driver.stdout` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_battery_summary.json` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_commands.jsonl` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_semantic_gate.json` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_semantic_gate.log` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_semantic_gate.ok` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_semantic_gate.receipt` `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_summary.json` `checks/audit/9a1459fe40d0-combined-current/checks/task_tests.xml` `checks/audit/9a1459fe40d0-combined-current/progress.log` `checks/audit/9a1459fe40d0-combined-current/result.json`

### Assessment or prior finding

## 9a1459fe40d0

**No issue found** in the bounded current audit of assigned generator SHA-256 `55f725bfacf1db458e29cb59c5b3e3cf30367a9a7f8e339c280aad2e9ca52356`, selected rule hash `1ed249363e20`.

I inspected the fold/occupancy-XOR implementation, its validators, exact profile controls, executable rivals, and the canonical-fitting `raw_value_inequality` shortcut. I then ran the source-bound combined audit preset. All **7/7** task tests passed. The strict semantic gate accepted **600/600** generated inputs and **3/3** canonical inputs; all six declared witnesses fired in every band; 12/12 two-demo lessons were identifiable; and **0/36** diagnostic held-out query rotations were ambiguous. The different-colored doubly occupied control refutes literal color inequality while preserving occupancy equality.

Evidence: `checks/audit/9a1459fe40d0-combined-current/result.json` and `checks/audit/9a1459fe40d0-combined-current/checks/9a1459fe40d0_audit_semantic_gate.json`. The run emitted a legacy test-import warning for `scripts.canonical_profile_gate`; that is test-maintenance debt, not a reproduced semantic or generator defect.

This is bounded evidence against the declared and generic tested rivals, not universal approval. The audit target was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## Native parametric reviewer build (2026-10-25)

Added a separate `mark_policy=project_right|occupied_side` family under
`workspace/parametric/`. Production generator and canonical authority remain
unchanged. Constructive lessons include both XOR directions and same-/different-
color doubly occupied controls. The maximum natural stress surface is 30×29
because equal halves plus one center divider require odd width. Native
qualification, protected-Racket causal replay, and owner acceptance are separate;
this note makes no training-admission claim.
