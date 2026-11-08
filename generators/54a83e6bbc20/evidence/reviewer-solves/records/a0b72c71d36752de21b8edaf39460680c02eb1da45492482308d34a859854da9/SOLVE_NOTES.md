# Visible-example solve work log

This is a concise reviewer-authored work log, not a captured token-level model
trace or a blind evaluation. I previously read and modified this task's generator
and read its Racket rule during the review. During this solve phase I read only
`challenge.json` and my own solution and feedback; I did not consult the generator,
Racket, previous solution explanations, reference implementations, or private
query labels.

## Revision 1

The three visible examples preserve the repeated cyan components at the left.
Each colored component on the right moves to the cyan component that it completes
into a solid rectangle. Background cells remain background elsewhere. Shape,
rather than row order or area alone, selects the matching component. All three
rows participate in the shape comparison.

I implemented connected-component extraction, inferred the repeated anchor color
and background, and used total foreground area divided by anchor count and common
height to infer the common rectangle width. A normalized missing-cell set must
match exactly one unused candidate. Each completed rectangle is painted at the
anchor's original position. The function rejects nonrectangular inputs and
nonunique matches rather than returning a guessed assignment.

The visible training pairs are the test oracle for this attempt. I am submitting
this first genuine implementation directly to the provided checker; I have not
invented an unsuccessful revision or a deliberate negative example. No query
correctness claim is possible from the masked challenge.
