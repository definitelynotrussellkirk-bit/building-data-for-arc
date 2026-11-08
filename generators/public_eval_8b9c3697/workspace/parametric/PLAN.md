# Public 8b9c3697 implementation plan

Goal: general socket docking reference and nearest/farthest episode family.

A detects a comb's full spine, two long guards and shorter middle tooth under
all four orientations. Its input-dependent middle width and tip locate the
matching red-rectangle ray. B selects the nearest (canonical) or farthest
compatible rectangle, erases other red objects, docks the selected rectangle
against the short tooth and paints its swept trail black. This preserves the
original's size/alignment matching and multi-object movement.

- [x] Fail official-label and API tests before implementation.
- [x] Implement independent Python geometry and general Racket reference;
      execute all three training pairs and supplied test gold.
- [x] Construct two to four independently oriented sockets, exact-width and
      incorrect-width near/far candidates, size-order-reversing demonstrations,
      2..6 demos and four shuffled distinct queries, including 30x30 scenes.
- [x] Reuse the task-local unapproved preflight/audit/export tool, retain the
      wrong-long-tooth causal witness and strict privacy/tamper evidence.
- [x] Review, final tests and exact-source authoring preflight, then hand off
      owner registration/qualification/acceptance separately.

Focus: genuine nearest matching object rather than nearest arbitrary red object;
negative coordinate projections for up/left; mismatched candidates removed;
exact swept interval and dock depth; no cross-socket stream interference;
setting-neutral inputs and stable demonstration/query RNG domains.

Completed inline with author self-review (no independent subagent). All checks
are bounded authoring evidence; owner admission remains explicitly pending.
