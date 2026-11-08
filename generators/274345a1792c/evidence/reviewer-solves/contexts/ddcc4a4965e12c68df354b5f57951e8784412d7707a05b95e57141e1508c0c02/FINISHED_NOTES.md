# Exposed solve work log

This is an assistant-authored work summary, not a token-level model trace.
Earlier exposure: yes. I inspected and repaired this task's generator and saw
its rule before starting this episode. During the episode I consulted only the
preparation's visible examples, the visible challenge, my new standalone Python
program, and the public visible-example check. Generator source, Racket source,
reference solutions, previous explanations and private labels remained closed.

## Revision 1

The visible outputs copy the maroon silhouette in cyan to every magenta anchor.
The symbol immediately above the anchor selects its orientation. The asymmetric
seven-cell examples distinguish the four operations: identity, clockwise quarter
turn, left-right reflection, and reflection followed by a clockwise quarter turn.
Repeated symbols receive repeated stamps, and an anchor stays magenta when the
corresponding transformed bounding-box corner is empty. The original silhouette,
controls, dimensions and unstamped background remain.

I wrote a standalone Boolean-mask implementation, using matrix reflection and
rotation and collecting anchors from the original input. The first example's
straight line is insufficient to distinguish all orientation rules; examples 1
and 3 provide asymmetric shapes and all four controls. Example 2 checks empty
bounding-box corners and repeated identity controls. I then requested the check
on all four demonstrations; no earlier failed program was attempted.

Multiple prototypes, unknown control symbols, or a different color-role grammar
are not determined by these examples. The two query predictions are submitted
for independent scoring; their correctness is unknown locally. Earlier rule
exposure means this episode is not claimed as a blind solution.
