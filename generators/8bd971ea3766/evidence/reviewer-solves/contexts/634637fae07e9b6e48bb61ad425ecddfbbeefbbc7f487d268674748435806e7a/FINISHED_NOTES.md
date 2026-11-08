# Solve work log

## Exposure declaration

Before this exposed solve, I had inspected and repaired the assigned generator and had therefore seen the canonical task rule. After `solve prepare` froze the final generator bytes, I did **not** reopen the generator, Racket rule, reference solution, private query labels, or earlier solve notes. This solve was written from the newly materialized `challenge.json` and its visible examples only. The final record therefore declares earlier exposure `yes` and reference consultation during the solve `no`.

## Revision 1 — exact horizontal sandwich completion

The changed cells in all three visible demonstrations are zeros whose immediate horizontal neighbors are the same nonzero color. Every original row window `[a, 0, a]` becomes `[a, a, a]`. The outputs leave unequal flanks such as `[2, 0, 3]`, longer gaps such as `[6, 0, 0, 6]`, isolated colors, and vertical arrangements unchanged. Example 0 also shows more than one target in a row, so all qualifying windows must be handled rather than only the first. I interpret windows from the original input and write their centers into a copy, which also handles overlapping windows such as `[2, 0, 2, 0, 2]` simultaneously.

I first added tests for all visible demonstrations, overlapping targets, non-target distractors, immutability, and the two frozen query predictions. With the supplied stub, all five tests failed at `NotImplementedError`, confirming that the tests exercised missing behavior rather than an existing implementation. I then implemented the minimal row scan.

Visible-example result: all demonstrations pass. The two predicted query outputs alter only the exact horizontal matching-flank centers:

- Query 0: `(3,5)=2`, `(4,1)=2`, `(4,5)=3`.
- Query 1: `(2,5)=7`, `(3,1)=8`, `(3,5)=6`.

Alternatives rejected from visible evidence: filling between matching colors at arbitrary distance; using unequal nonzero flanks; applying the rule vertically; or stopping after one match per row. Remaining uncertainty is limited to private examples outside the visible domain; the visible set directly distinguishes each of those nearby alternatives.
