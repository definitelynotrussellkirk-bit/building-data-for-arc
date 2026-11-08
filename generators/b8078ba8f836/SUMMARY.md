# b8078ba8f836 — Complete the Segments

For each nonzero color that occurs **exactly twice**, fill the inclusive straight segment between its two cells when they share a row or a column. Leave diagonal pairs, singletons, and colors occurring three times unchanged.

Version `3.0.0` samples 8–12 by 8–14 inputs with one or two horizontal pairs, one or two vertical pairs, and zero to two singleton colors. Its three-step lesson schedule is `canonical, counterexample, counterexample`. A counterexample scene contains both an unaligned exact-two color and a three-cell color with one aligned subpair, so the alignment and exact-count predicates are demonstrated rather than merely stated.

All six advertised axes are exact and recoverable from pixels. Eligible segments are disjoint and protected from distractors. The canonical Racket rule is unchanged and pinned by `RULE_HASH = "48fc6f20bbde"`.

Kind: `per_puzzle`. Current generator version: `3.0.0`.
Approval remains catalog/maintainer controlled; passing review checks does not admit training data.
