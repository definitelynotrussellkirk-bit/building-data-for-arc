# Working notes: generic_waypoint_route_gen1

The standalone `reference.rkt` preserves the exact existing embedded `PROGRAM`:
program SHA-256 `151b92a1061d985d8cd21e3dbc8ddea3a8f01bdffe7365b618d5adf2571144f3`,
normalized rule identifier `ad2fb3607800`. `generator.py` remains unchanged at
SHA-256 `b0c6b063ee8f18c10ddaefc8692939d88365692671eb8d255e0ced0b596cc3bc`.
The rule selects the final panel, follows its unique row/column-aligned sequence
of remaining waypoints, and renders the cursor at the final waypoint with its
orientation determined by the final leg. This is a semantic variant inspired by
evaluation task `5545f144`, not a solution or canonical record for that original.

The task-owned canonical candidate in
`evidence/canonical-reference/canonical-record.json` has three demonstrations
from easy/medium/hard draws and four distinct two-step query witnesses, one per
final heading. Every retained label was executed through the real Racket
reference. `workspace/validate_reference.py` reproduces the candidate and bounded
checks against its registered canonical row. Tests read the current tree's
canonical ledger through `reviewer_support` and do not require retained
`evidence/` files in the portable task-test snapshot. The initial local test
source and manifest remain in `evidence/canonical-reference/provenance/`; the
original 61-evaluation receipt is unchanged historical evidence. The current
public `task_tests` check executed 20 tests successfully after the evidence-path
portability correction. The evidence manifest binds these distinct checks to
their source bytes. Four fixed queries here do not change `generate_task`'s current
hardcoded three-demonstration/one-query API: the worker visibly rejects a request
for four queries instead of returning a short episode. This evidence does not
claim four-query generation support or create a production parameter API.

The existing dead-context audits remain **unresolved**: only the final panel
affects the answer, and erasing earlier panel contents is accepted by the
current structural checker. The new bounded probe reproduces this limitation.
The two-step witnesses establish waypoint chaining and final-leg orientation
inside the last panel; they do not establish dependence on earlier panels.
Reference registration enables review tooling; it grants no approval, does not
clear audit findings, and does not admit trajectories to training.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
