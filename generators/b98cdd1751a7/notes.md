# Working notes: b98cdd1751a7

## Current parametric family

- Owner-accepted `bottom_order` has three settings: `left_right` (exact canonical default), `match_top_left_color` (preserved exact program), and `fewest_cells_first` (exact incoming program). One existing family gained one setting.
- All settings share two distinguishing demonstrations. The first combines the incoming offset-row geometry with the existing paired-color cue; the second preserves the opposite color contrast. Query banks rotate by seed independently of setting and requested counts. Supported counts are 2–6 demonstrations and 1–4 queries; normal training requests four private queries, revealed separately.
- The bounded reconciliation audit passed 386 protected-Racket evaluations and the declared rival checks at seeds 0/17 with 2/6 demonstrations. Matching inputs and count/public prefixes passed. Six affected loader tests passed; previous source-containment and hash assertions were preserved.
- Fresh owner qualification passed six jobs with two demonstrations, four queries and 60 protected evaluations; native acceptance replay passed on the final source. The owner also replayed the wrong-midpoint causal case. Current hashes, scope and exact-source evidence are in `evidence/owner-sampler-reconciliation/current.json`. These checks do not establish unrestricted uniqueness or learning benefit.
- Production `generator.py` remains the approved SHA-256 `5588e75560f52086dc2e80c063320e0e6318672fb64b4470d5bcd5a3d1cfb5b1`. The incoming whole delta was deferred because it conflicted with the existing accepted family; the owner union was accepted separately.

## Open canonical work

The authority-pin/default-distribution repair remains a runnable proposal in `workspace/canonical_repair_proposal/` (proposal SHA-256 `02fab8bf64a8d4e23ab44712cc81ed537c74b09923d9a9330796b5eeac83edd1`; 72 tests reviewer-reported). It is not active. Applying it requires canonical re-approval and fresh native qualification/acceptance. The open production audit remains unresolved; parameter-family acceptance does not clear it or admit trajectories to training.
