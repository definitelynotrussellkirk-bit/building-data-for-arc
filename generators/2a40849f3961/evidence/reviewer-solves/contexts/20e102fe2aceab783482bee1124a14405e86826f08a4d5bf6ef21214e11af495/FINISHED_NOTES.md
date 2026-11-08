# Visible-only solve: 2a40849f3961

Earlier exposure: none. Before this solve I read only packet workflow instructions
and the displayed public challenge. No generator, rule, canonical helper, notes,
audit evidence, reference solution, or masked-query answer has been opened.

The visible examples preserve all original cells and add color 8 to connect the
single markers 1, 2, 3 and 4, in numerical order, around walls of color 5.
The routes look shortest in the four-neighbor grid. Paths can overlap. Example 0
has equal-length detours above and below one wall and takes the upper detour;
example 1 takes the left detour around a centered horizontal wall. This supports
breadth-first search with neighbor order up, down, left, right. The three paths
are computed on the original grid and only original zero cells are recolored.

Revision 1 implements this hypothesis with a queue and predecessor map. The
dimensions are 11×12, 11×13 and 12×12 for the three visible input/output pairs.
The two masked query inputs are 11×12 and 11×13; output dimensions are unknown
in the challenge. The program proposes same-size outputs as in the examples.

Planned check: the packet's visible-only checker, intent=solve. Remaining
uncertainty: the examples may not identify every possible route tie-breaking
policy; no private query correctness claim is possible here.

Revision 1 checker result: completed, 3/3 visible examples passed. No query labels
were provided. Stopping with this consistent shortest-path hypothesis; no revisions
were needed. This is an authored work log, not a token-level trace.
