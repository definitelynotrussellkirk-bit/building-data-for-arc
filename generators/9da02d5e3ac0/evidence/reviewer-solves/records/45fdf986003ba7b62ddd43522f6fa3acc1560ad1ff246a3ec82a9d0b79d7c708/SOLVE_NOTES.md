# Solve work log

This is a human-visible-example solve record. I had earlier rule exposure from reviewing this task, so the final declaration is `yes`; during this solve I did not reopen the generator, Racket rule, reference solutions, private labels, or the prior solve explanation.

## Revision 1 — row-local first non-5 key

The three demonstrations are shape-preserving:

- Example 0: 13×12 → 13×12.
- Example 1: 12×16 → 12×16.
- Example 2: 13×12 → 13×12.

Within each row, non-5 cells stay fixed. Every 5 changes to the first value in that row that is not 5. This includes two important visible edge cases:

1. Rows beginning with `0` use 0 as the key, even when a later colored cell is present; their 5s become 0.
2. A row made entirely of 5s has no key and remains unchanged.

The interior-key rows rule out a fixed-column interpretation: for example, a row beginning `[5,5,5,6,...]` uses 6 even though the key is not in column 0 or 1. The implementation scans each row from left to right for the first value unequal to 5, then replaces only the 5 cells.

No failed natural solve revision preceded this one. Query correctness is withheld; I stop after checking this single hypothesis against all visible demonstrations.
