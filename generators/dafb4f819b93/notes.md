# Working notes: dafb4f819b93

## Current decision

Retain the approved production generator and canonical rule unchanged. The task-local
proposal under `workspace/parametric/` adds one episode-fixed rule parameter:

- `rank_delta = 0` is the canonical/default behavior, byte-for-byte the canonical
  Racket source: fill an interior zero when its right-border row label and
  bottom-border column label have equal rank in their shared ordered palette.
- `rank_delta = 1` is the proposed nearby behavior: fill with the row label when
  its rank is exactly one later than the column label's rank.

The border roles, ordered-palette recovery, preservation of nonzero cells, and
row-label paint source remain invariant. Only the comparison relation changes.
The prototype is proposed and unapproved; it does not change catalog approval or
training admission.

## Retained evidence

Seed 31 materializes both settings with two demonstrations and four distinct
queries per episode. All 12 labels come from the matching exact Racket program;
the independent Python mirror agrees; both episodes reject the other setting on
demonstrations and all eight queries differ under the rival. The default program
hash is the canonical
`fd28f01b9690c2b68a529d5ecb88df555c53e93cc5254d1f6662017f1fdcf6cc`;
the proposed program hash is
`d3ef521dfc18c58fe6eec0c3a2ee99a5eb8411507f094809072ed1e64186d01a`.
See `checks/parametric/dafb4f819b93-rank-delta-v1/`.

The bounded adversarial pass exercised one demonstration plus the maximum 12
queries, seven invalid numeric/count cases, clean-tree replay, and public-input
tampering. It found no defect in those surfaces; this is not an exhaustive seed
or malformed-tree census. See
`checks/parametric/dafb4f819b93-adversarial.json`.

The frozen selected test was repaired only for portable source/canonical lookup:
it now uses `reviewer_support` rather than a nonexistent staged package import
and fixed parent-depth path. The production generator remains at SHA-256
`76a6435587f8b973716e6581f0f99cdec9e1e7c88c992aef3e8e51ffb6cb91c3`.

## Limits / next useful action

Evidence covers only `rank_delta` values 0 and 1, two primary episodes, and the
other declared setting as the lesson rival. A maintainer can evaluate whether
this semantic axis belongs in a future production parametric API; packaging this
prototype alone is not such an approval.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/dafb4f819b93/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

Ported the additive semantic teaching contract without changing existing generation or VERSION. Retained current non-cyclic rank_delta prototype and added the distinct cyclic next-label label_offset module beside it; prior reviewer receipts remain prior-source evidence and focused current-source checks are separate.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->
