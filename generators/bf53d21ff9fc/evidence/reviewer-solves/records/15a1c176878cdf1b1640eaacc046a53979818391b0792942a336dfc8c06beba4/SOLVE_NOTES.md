# Solve work log

## Exposure declaration before solving

I had already reviewed this task's generator and canonical-rule material during the
repair phase, so this is an exposed post-repair solve. During this solve phase I
did not reopen the generator, Racket rule, reference solutions, private labels,
or earlier solution explanations. I used only the visible examples in
`challenge.json` and the visible-only check feedback.

## Revision 1 — route consumption and penultimate relocation

Across the three visible examples, a gray `5` changes only when it touches a
green `3` chain. The chain is erased to orange `7`, except its far endpoint stays
green, and the gray marker appears one cell before that endpoint. The marker's
old cell becomes orange. Gray markers not touching a green chain remain fixed;
zeros and disconnected green components remain fixed.

For multiple markers, I treat the input as the route map for every marker while
accumulating edits in one output. I scan markers row-major and trace cardinal
neighbors in a fixed up/down/left/right order, excluding the immediately prior
cell. The visible paths are simple, but I bound the walk by the larger grid
dimension so malformed cycles cannot run forever. A one-cell green attachment
is left unchanged because there is no distinct endpoint and penultimate cell.

Alternative hypotheses rejected from the examples:

- moving gray to the final green cell: visible outputs retain the final green and
  put gray immediately before it;
- preserving the route behind the moved gray: visible outputs clear it;
- deleting every gray: isolated markers survive;
- using progressively edited output to discover later routes: the examples are
  more naturally explained by a common original route map.

Remaining uncertainty is limited to unseen branch/cycle tie cases; the visible
examples support the fixed cardinal traversal used in `solution.py`.
