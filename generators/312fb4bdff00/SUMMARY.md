# 312fb4bdff00 — ordered, translation-normalized prototype matching

Version: `3.1.0`. Generator SHA-256:
`e2d85dedd4b4a2fb2a5bacb6c24ea9c25113bd95ba52917e7410449e376c3c97`.
Canonical rule pin: `cc8c5c7301a4`; Racket authority is unchanged.

The header supplies the output color. Full-height color-8 columns split the body
into one query and 1–4 candidate square panels. Compare occupied supports after
translation normalization under the ordered eight D4 transforms. Return the
first matching transformed candidate in its own full-panel position, recolored
to the header target. With no match, return `[[0]]`.

The default three-phase curriculum is now deterministic: multiple matches,
absence, translated single match. A six-pair lesson contains two of each, so any
five-demo cyclic holdout retains a no-match sentinel example as well as
translated-match and precedence evidence. Seven canonical-fitting rivals are
explicitly declared, including the repaired `copy_query_on_absence` failure.
Exact overrides remain per-input controls and do not promise the default lesson
schedule. `workspace/README.md` documents reproduction and limits.

Approval remains a catalog decision; passing this review does not admit training.
