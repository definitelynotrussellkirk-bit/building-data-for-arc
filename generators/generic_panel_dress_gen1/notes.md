# Working notes: generic_panel_dress_gen1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-38a14d486cbd6b35:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `4d334d35eb30d0b798220259917fa2e082b8b6834152cd826b376640e4fbf64d`. At disposition, audited bytes match the current source.

### Current decision

Explicit bounded disposition of the older parity audit only: 102 reference comparisons and 300 tasks/1275 pairs had unique keys; reading order matched 294/1275 pairs. Those results do not establish that every complete episode refutes reading order. The new exact seed14 episode counterexample in review-0daf74b2dce0d3b4:v0001 remains independently unresolved. No blanket clean-teaching conclusion.

### Assessment or prior finding

## generic_panel_dress_gen1

No issue found after checking.

I ran the generator's Racket/Python parity harness: **102/102 generated pairs were byte-exact**. I then stress-generated 300 tasks across easy, medium, and hard, comprising 1,275 input/output pairs. Every pair had a one-to-one set of unique panel dot counts and shape hole counts, so the intended count key was always defined. A plausible scan-order shortcut paired panels and shapes correctly on only 294/1,275 pairs (23.1%), so placement order does not replace the hole-count relation. Field color, panel colors, shape colors, orientations, and placements vary by keyed RNG. There is no canonical row for this generic concept, so this conclusion is limited to its declared concept contract plus execution parity rather than external canonical examples.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
