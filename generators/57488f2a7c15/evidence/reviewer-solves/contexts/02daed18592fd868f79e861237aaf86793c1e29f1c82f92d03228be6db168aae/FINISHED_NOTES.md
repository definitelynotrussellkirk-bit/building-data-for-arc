# Post-repair visible-only solve

This is an exposed solve: I previously reviewed and repaired this task's generator and saw its rule. After `prepare`, I kept generator source, reference rule, prior solution explanations, and private labels closed. I read only `solve/challenge.json` for the solving phase. I did not consult a reference during this phase.

## Revision 1 — retain sources and reflect across the main diagonal

The five visible examples preserve square size and every original colored cell. Additions exchange row and column: for example, the first 5×5 example copies the 9 at (3,0) to (0,3), while its diagonal 5 stays in place and the other 5 is copied from (3,2) to (2,3). The fourth example contains only upper-triangle sources, and each appears below the diagonal too. The second and fifth examples show both source directions; matching a diagonal cell's color does not exempt another source from copying.

Hypothesis: copy the input and reflect every nonzero cell to (column,row), keeping its color. The demonstrations show no conflicting occupied reflection partners, so I make no claim about resolving such an unseen conflict.

A visible-only Python probe compared this hypothesis with transpose-only, lower-only, horizontal-reflection and vertical-reflection alternatives. It read just the five visible input/output pairs. Query outputs were neither available nor inspected. Results are retained in `checks/post-solve-visible-probe.json`:

- proposed: 5/5 visible pairs; mismatched cells [0, 0, 0, 0, 0].
- transpose_only: 0/5 visible pairs; mismatched cells [3, 3, 3, 4, 4].
- lower_only: 1/5 visible pairs; mismatched cells [0, 2, 1, 4, 3].
- horizontal_reflection: 0/5 visible pairs; mismatched cells [5, 7, 6, 8, 9].
- vertical_reflection: 0/5 visible pairs; mismatched cells [6, 7, 6, 8, 9].

The proposed rule matches every visible pair. This is one genuine solution revision, with alternatives evaluated as diagnostic hypotheses rather than submitted failed solves. Next I will run the required visible-example and execution check. Hidden-query correctness remains unknown.

## Check and stop

The required check completed execution and reported 5/5 visible examples matched for revision 1. It withheld hidden-query correctness (`reported_label: unknown`). No visible mismatch remains to motivate another revision; I stop after this single genuine attempt. Earlier rule exposure is yes, and reference consultation during this solving phase is no.
