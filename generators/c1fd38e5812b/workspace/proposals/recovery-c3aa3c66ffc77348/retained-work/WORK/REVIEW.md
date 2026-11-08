# Review: generator c1fd38e5812b

1. The authoritative rule is independent run compression: row starts come from the first column and column starts come from the first row.
2. The selected canonical program normalizes to `(rule! (compress-grid g))` and hashes to `0805714fcf25`; the generator's prior `dc8aa1222f34` pin was stale.
3. The prior generator covered both axes uniform and both axes nonuniform, but never uniform rows with nonuniform columns or the converse.
4. That omission admits a reproducible shortcut: a learner can couple row and column regularity and still fit every generated lesson.
5. Added `uniform_rows` and `uniform_cols` profiles, independently generated and independently observable across easy, medium, and hard bands.
6. Rebalanced profile weights to keep public-derived lessons at 25% and fully uniform lessons at 10%, while assigning 10% to each mixed-axis profile.
7. Added a concrete 6-by-2 logical witness whose row spans are all 2 and column spans are 4 and 8; coupled chunking incorrectly returns a third column.
8. Replaced repository-relative test discovery with `reviewer_support.find_root`, fixing the portable task-test failure.
9. Added regression tests for mixed-axis generation, observation, oracle agreement, counterexample separation, distribution, determinism, and the authority hash.
10. Added a six-member Racket-backed parametric family varying compressed axes and optional transpose, with rival-refuting demonstrations and exactly four distinct queries.
11. The blind task was solved and frozen before generator/reference inspection; the visible-only solution passed all three examples in the original run.
12. Local reconstructed tests are green; official packet battery, audit, visible-only solve, and packaging must be rerun in the original packet because its 350 MB attachment could not be rematerialized after the execution workspace reset.

## Root cause

The profile taxonomy treated run regularity as one joint property (`uniform_runs`
versus `nonuniform_runs`) even though the rule detects the two axes through
separate signals. The tests mirrored that taxonomy, so no generated example or
test could expose an illicit coupling between axis assumptions.

## Repair

The repair makes axis regularity explicit in analysis and generation, pins the
canonical authority hash, and makes tests portable. It deliberately avoids
changing the rule, public-derived profiles, input size contract, color contract,
or first-row/first-column boundary semantics.

## Public-evaluation transfer

Task `cb2d8a2c` suggests a useful separate family in which unary marker count
controls path clearance around sequential barriers. That mechanism is not
integrated into this generator: doing so would mix routing semantics into a
run-compression grammar and reduce interpretability. The transfer proposal is
to build it as a distinct parameterized routing family, not as a profile here.
