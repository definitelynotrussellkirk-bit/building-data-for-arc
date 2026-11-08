# Post-repair visible-only solve

This is a concise authored work log, not a captured token-level conversation.
I had earlier exposure to the canonical rule and generator during the repair.
During this solve I used the newly prepared public challenge and my Python
solution only; I did not reopen the rule, generator, reference solutions, prior
solution explanations, or private labels. Hidden-query correctness is unknown.

## Visible observations

- Example 0 — Input: 7 rows × 11 columns. Output: 7 rows × 11 columns.
  Both routes between the colored endpoints acquire 8s, while part of the
  connected open perimeter remains 0. Painting the whole component is wrong.
- Example 1 — Input: 7 rows × 11 columns. Output: 7 rows × 11 columns.
  Four open cells become 8 even though any one shortest route has only two
  intermediate cells. The output combines tied shortest alternatives.
- Example 2 — Input: 23 rows × 15 columns. Output: 23 rows × 15 columns.
  The long corridors retain walls and endpoints; the remote detour stays 0.
- Example 3 — Input: 9 rows × 15 columns. Output: 9 rows × 15 columns.
  Start (1,12) and goal (2,11) have two cardinal routes; both intermediate
  cells are painted. A diagonal step or one chosen cardinal route is insufficient.
- Query 0 — Input: 7 rows × 11 columns. Output: unknown.
- Query 1 — Input: 8 rows × 13 columns. Output: unknown.

## Revision 1

Hypothesis: preserve the input except for zero cells belonging to at least one
shortest cardinal route from 2 to 3 through non-wall cells. Use unit edge costs.
The implementation stores every predecessor at the minimum BFS distance and
walks that predecessor graph backward from the goal. It therefore includes all
ties while excluding longer routes. This is a fresh implementation for the
visible solve; earlier exposure means this record is not blind.

The local visible-only experiment checks all four given outputs and confirms
shape preservation and the exact changed-cell counts. The protocol checker will
retain this first actual revision. No failed attempt or deliberate negative has
been manufactured, and query predictions are not inspected.
