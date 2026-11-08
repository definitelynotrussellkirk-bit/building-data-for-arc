# Feedback to Codex

F1: Protected-Racket numeric division semantics are easy to misread

The spacecraft direction rule initially failed one official label because `/` in this protected DSL performed integer division, collapsing cross-section averages that the Python mirror treated as fractional. Document a canonical `mean` helper or add an authoring-preflight warning for `/` used in geometric averages; the concrete fix here was to force inexact arithmetic with `(+ 0.0 ...)` before division.

F2: Changed-target receipts retain far more runtime inventory than the task needs

Each focused `task-tests` receipt binds hundreds of shared runtime files even though the task-local source binding and a protected-runtime aggregate identity are sufficient for this review. Retaining a task-local file list plus one runtime-manifest digest would make source-bound evidence smaller and easier for later agents to inspect without weakening drift detection.
