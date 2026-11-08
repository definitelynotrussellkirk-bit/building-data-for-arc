# Exposed visible-example solve

This is an assistant-authored work log, not a token-level model trace. I had
earlier exposure to this task's rule and generator during the required repair.
After preparing this episode I consulted only the public challenge, its README,
the starter solution, and solve command help. I did not consult the reference
program, generator, reference solutions, prior solution notes, or private answers
during this solve phase. This is not a blind or independent discovery claim.

## Visible evidence and hypothesis

The visible outputs are unchanged rectangular pieces of their inputs. All
color-9 cells are retained, and their minimum/maximum row and column coordinates
give the exact output extent. Other colors inside that rectangle stay intact;
other colors outside disappear.

| Visible pair | Input dimensions | Output dimensions | Inclusive input bounds, zero-based |
| --- | --- | --- | --- |
| Train 0 | 8 rows × 9 columns | 4 rows × 4 columns | rows 0..3, columns 3..6 |
| Train 1 | 8 rows × 9 columns | 6 rows × 4 columns | rows 0..5, columns 2..5 |
| Train 2 | 8 rows × 9 columns | 3 rows × 3 columns | rows 4..6, columns 6..8 |
| Train 3 | 14 rows × 10 columns | 11 rows × 7 columns | rows 3..13, columns 2..8 |

Train 1 uses four markers on different sides, so every marker contributes to
the extrema; a single diagonal pair is insufficient. Train 2 reverses the
diagonal. Exterior nonzero cells in the examples rule out trimming the bounds
of all nonzero content. The varied nonzero counts in Train 1 and Train 3 make
simple frequency selection implausible; the code selects the observed color 9.

## Revision 1

Implement `solve(grid)` by collecting all color-9 coordinates and slicing the
inclusive bounding rectangle. Preserve every cell value inside. Raise a clear
error for an input with no markers, a case not shown in the visible challenge.

The supplied starter raised NotImplementedError. I replaced it before the first
check; it was not submitted as an attempted solution and is not a natural
failure record. There are no fabricated negative attempts.

Query 0: Input: 9 rows × 10 columns. Output: unknown.
Query 1: Input: 9 rows × 10 columns. Output: unknown.
The checker may confirm visible examples and execution, but hidden query
correctness remains unknown in this record.

The first check completed successfully: 4/4 visible examples matched and both
query executions completed. No hidden correctness score was returned. I am
stopping after this single actual revision because the visible examples are
consistent with the implementation and further changes lack visible evidence.
