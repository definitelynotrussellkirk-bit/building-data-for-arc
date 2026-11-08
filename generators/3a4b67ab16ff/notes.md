# Working notes: 3a4b67ab16ff

## Current decisions

- Preserve the canonical bbox/intersection rule and canonical ledger unchanged; production remains `RULE_HASH=32c694357bd0`.
- Close the main teaching shortcut with `distributed_extrema`: four non-corner markers establish top/left/right/bottom collectively, so first/last row-major markers do not recover the bbox.
- Keep the new profile inside the gray rectangle to isolate the intended lesson from clipping/projection complications.
- Raise exact-public sampler weight from 2 to 5. Weight 3 restored one anchor per band but still missed the repository's 25% total canonical-envelope floor; weight 5 passes at 17/60 with easy/medium/hard support 7/5/5.
- Reject non-exact integer seeds/sample indices and negative sample indices after defect-lint exposed Python bool/float/string acceptance.
- Keep `layer_order={ascending,descending}` in `workspace/parametric/` only. Ascending is the exact canonical source; descending changes only color iteration. Each retained episode fixes one setting and has 3 demonstrations plus 4 distinct Racket-labelled queries.
- Public prototype exports use exact `reviewer_support.public_challenge_bytes` and content IDs; private settings, seed, programs, rivals, and query answers stay separate. The batch is now fully validated before output creation, duplicate visible payloads fail before any public write, and physical public emission is sorted by visible ID.

## Evidence and unresolved items

This packet's prototype-only edit passes `20` focused layer-order tests and `35` selected edit-scope tests. Fresh seed-start-1 evidence retains one Racket-backed episode per setting, each with 3 demonstrations and 4 distinct queries; the visible IDs are emitted in sorted order. Earlier production lint, self-check, override, profile-floor, defect-lint, and rule-smoke receipts remain source-bound to the unchanged production generator.

The aggregate selected-task directory still cannot collect the issued frozen production fixture because it imports the absent staged module `puzzle_generators.per_puzzle.3a4b67ab16ff`; that blocked aggregate is retained rather than counted as a pass. The next useful maintainer action is to assess the layer-order family independently and, separately, make the frozen fixture source-packet portable if an aggregate task run is required.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/3a4b67ab16ff/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-public-order:start -->
## Current prototype public emission-order repair

Closed the retained export-order finding. `materialize` now precomputes every
Racket-backed episode and visible payload, rejects duplicate public IDs before
creating the output tree, sorts by `public_id`, and only then writes evidence.
The seed-start-1 regression deliberately makes private enumeration oppose
visible-ID order; both that case and duplicate-before-write rejection are pinned
in focused tests. Evidence: `checks/parametric/3a4b67ab16ff-layer-order-final/repair-summary.json`.
No production generator, canonical rule, variant approval, or training admission changed.
<!-- arcpuzzles-current-public-order:end -->

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

Retained current distributed_extrema grammar, sampler weights, strict scalar boundary and layer_order prototype. Ported the missing executable endpoint_only_bbox rival/witness binding using current profile naming. The parallel split_extrema rename/resampling and duplicate prototype were not selected; canonical rule formatting/authority were not changed.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->
