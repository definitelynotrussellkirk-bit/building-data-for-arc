# Final-source visible-only solve

This is a concise authored work log, not a token-level reasoning trace.
Earlier rule exposure: yes, during generator repair and the earlier exposed
solve. That earlier episode is retained in checks/prior-solve. This episode
was freshly prepared from generator SHA-256
0ba5665018235581095d844bd1ad759c0ee30fb5b9d36c4602bf5c45d130fd4e.
No generator, reference rule, private query label, canonical helper or previous
solution explanation was opened during this solve attempt.

## Visible hypothesis

Example 0: input 12 rows x 13 columns; output 4 x 4.
Example 1: input 19 rows x 19 columns; output 5 x 5.
Example 2: input 12 rows x 13 columns; output 4 x 4.
Query inputs are 17 x 18 and 10 x 12; outputs remain unknown.
The examples support a square relation table over the colored rectangles,
ordered first by their top row and then by their left edge when top rows tie.
A shared row contributes 1 and a shared column contributes 2; diagonal values
are 3. Inclusive one-cell projection intersections are visible in the examples.

## Implementation and checks

I wrote a fresh component-flood-fill implementation and computed overlap by
closed interval comparisons. It does not import any task or reference code.
The first implementation matched all three visible examples exactly in a local
check. The official check records the visible result and query execution only;
query correctness is withheld for maintainer scoring. No failed revision was
invented, and no further revision is justified by the visible evidence.
