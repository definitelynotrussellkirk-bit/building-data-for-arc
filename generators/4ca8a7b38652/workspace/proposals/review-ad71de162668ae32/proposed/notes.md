# Current notes: `4ca8a7b38652`

## Rule and distribution

Count distinct nonzero input colors, then replace each cell with a square block
of that size. Zero is copied but excluded from the count. The selected canonical
rule remains `RULE_HASH = "2e2cb8677499"`. Counts zero or one give identity;
generated teaching inputs deliberately use two through four nonzero colors.

The inherited version-3 sampler emits 3×3 grids, with exact controls color_count
(2–4) and zero_present (boolean). Zero-present frequency profiles cover canonical
examples; zero-free draws refute “all distinct colors minus one.” The five-position
schedule is (2,zero), (3,no-zero), (4,zero), (2,no-zero), (4,zero), phase-shifted
by seed and sample index. Five demos plus one query retain the declared contrasts
under a single holdout. The validator describes this narrow teaching manifold,
not the full Racket domain. No sampling choice changes in this review.

## Current repair

The inherited generator accepted boolean seeds/indices and negative indices.
The entry point now requires literal Python integer seeds and nonnegative literal
Python integer indices. Booleans fail with TypeError; negative integer seeds
remain valid. Axis and difficulty behavior, including None axis defaults, stays.

VERSION stays 3.0.0 to preserve valid RNG keys. Repaired source SHA-256:
`d37aae7cb061aee2b45ba081dd7ce5c1811adc35aaac3b5ed57200aae0fd1aac`.
The 64-request valid-output fingerprint is unchanged from baseline. Minimal
requests are in `counterexamples/invalid_request_scalars.json`; regression tests
are in `tests/test_request_scalars.py`. Accepted return
`review-4fb26919ebdecf32:v0001` was historical context, not fresh proof.
Cumulative old prose and stale version-2 SUMMARY are replaced with the current
account. Earlier authority synchronization remains intact; this review changes
neither canonical nor selected authority.

## Runnable parametric proposal

`workspace/parametric/prototype.py` selects one hidden episode offset in {-1,0,1}
and executes factor max(1,n+offset) in Racket. Offset zero is byte-identical to
the canonical program. Five ordered 3×3 demos teach the offset; a query is 3×3
or a new 6×6 arrangement with the same palette. Larger queries are outside the
canonical manifold. Public challenges contain no parameters or query answers;
private evidence retains programs, hashes and labels. Its README has commands.
This is a proposal, not a production API or approval of alternative rules.

## Verification and limits

The return retains a 12/12 green strict after battery, 61/61 portable task tests,
300 production lessons (1,800 pairs; 1,656 unique inputs) and 1,800 rotations with
no ambiguity against five unique declared rivals. All five starts at fixed seed
zero across three bands also pass: 15 lessons, 90 pairs, 27 unique inputs and
90 rotations. The final battery attaches that schedule receipt. Earlier failed
iterations remain in the return.

The proposal has 12 saved episodes, 72 primary Racket labels, parity on six
canonical pairs, and all 108 wrong-rival/episode combinations refuted by demos.
Prototype arbitrary rotations are untested. Finite rival checks do not prove
unique induction or canonical larger-grid generalization. No assigned-task
repair blocker remains; wider suite failures and audit findings are documented
separately. Review: `review-ad71de162668ae32`.
