# Solve work log

## Isolation and exposure

I began this solve from the packet's visible presentation only. Before finishing it I did not open the task's generator, Racket rule, canonical labels, reference solutions, audit records, or the repair target. I had no remembered prior exposure to task `5dc10de63325`.

## Revision 1 — complete groups of four

**Observation.** The spatial arrangements vary widely, but output shape is always 5×5. The number of azure input cells and azure output cells form buckets:

- input counts 4, 6, 7 → 4 output cells;
- input counts 9, 10, 11 → 8 output cells;
- input counts 12, 14, 15 → 12 output cells;
- input count 17 → 16 output cells.

Thus the output retains four cells per complete group of four azure input cells and ignores a remainder. Every output is four copies of the same 2×2 counter, separated by an all-zero middle row and column. Within each 2×2 copy, groups fill in the order lower-right, lower-left, upper-right, upper-left.

**Alternatives rejected.** Connected-component count and object shape do not explain the examples: solid and scattered inputs with the same count bucket produce the same output, and examples with very different connectivity share an output. Input coordinates, bounding boxes, and symmetry likewise vary without affecting the bucket.

**Probe.** I wrote a visible-example regression harness in `/tmp/test_blind_visible.py`. It failed first on the provided `NotImplementedError`, then passed all ten visible training pairs after implementing the count-and-counter rule.

**Queries predicted.** Query 0 has 12 azure cells, so it uses the three-cell 2×2 motif repeated four times (12 output cells). Query 1 has 9 azure cells, so it uses the two-cell motif repeated four times (8 output cells).

**Remaining uncertainty.** Visible data only exercises one through four complete groups. I cap the counter at four because the fixed 2×2 motif has four positions; behavior for fewer than four azure cells or twenty or more is not demonstrated.
