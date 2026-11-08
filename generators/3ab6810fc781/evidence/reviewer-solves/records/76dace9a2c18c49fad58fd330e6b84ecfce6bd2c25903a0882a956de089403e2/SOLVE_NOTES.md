# Blind solve work log — 3ab6810fc781

This is a reviewer-authored work log, not a token-level model conversation.
Earlier exposure: no known exposure to this task's generator, rule, notes, or solutions.
Only the visible challenge was opened before solving.

## Revision 1 — largest connected foreground object
The visible outputs are tight crops of individual foreground objects with their
original colors and interior zeros preserved. Counting foreground cells supports
selecting the largest object: training example 1 has object sizes 8, 7, and 5;
example 2 has 6, 4, and 2; example 3's selected object has 8 cells, versus a
seven-cell L and smaller distractors. A multicolor-only selection would not
explain example 3, and largest bounding box would prefer its seven-cell L.
Implemented four-neighbor connectivity over all nonzero colors together,
selected the maximum cell-count component, and cropped its bounding box.
The examples do not establish a tie policy or discriminate every connectivity
convention; the implementation uses deterministic scan-order ties.
No deliberately incorrect revision was created.
