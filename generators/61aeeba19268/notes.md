# Working notes: 61aeeba19268

## Current decision

Keep the base generator and canonical Racket rule unchanged. The native family adds one finite setting beside the exact canonical default:

- `sweep_only`: exact canonical horizontal sweep.
- `sweep_then_drop`: sweep first, select the unique non-marker 7 cue that becomes orthogonally adjacent only in the swept intermediate, then draw a source-colored vertical ray from that cue to the bottom edge.

The construction uses matched inputs across settings, 2–6 demonstrations, four distinct queries, source/cue variation, left/right cue decoys, and one substantive 30×30 query. The minimum two demonstrations reject the bounded rivals `sweep_only`, `original_adjacency`, `rightmost_cue`, and `fixed_w_minus_2` for all 64 audited seeds.

## Evidence and limits

- Self-review: `workspace/parametric/evidence/current/self-review.json` — 192 setting-paired episodes, 2,944 labeled pairs, 192 exact 30×30 queries, zero named-rival survivors.
- Inventory: `workspace/parametric/evidence/manifest.json`.
- Authoring preflight: `checks/61aeeba19268/qualification/qualification.json` with 32 protected-Racket evaluations.
- Causal replay: `checks/61aeeba19268/causal/witness.json`.
- Public projection/privacy: `checks/61aeeba19268/preview-verify.json` and `checks/61aeeba19268/first-turn.json`.

This is a finite reviewer-ready prototype, not owner acceptance, universal uniqueness evidence, or training admission. The next action is exact-source owner review followed by unchanged native qualification and acceptance.
