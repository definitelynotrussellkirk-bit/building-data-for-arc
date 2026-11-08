# Visible-only solve notes

All three demonstrations preserve shape and every original nonzero cell. The only additions are magenta `6` cells immediately before and after maximal horizontal yellow `4` runs of length exactly three. Yellow runs of length two, four, or five are unchanged, and non-yellow length-three runs (the `9` and `5` controls) are unchanged, so the trigger is both color-specific and exact-length rather than “any triple” or “at least three.”

Revision 1 implements one left-to-right maximal-run scan per row. It adds a cap only when the adjacent cell exists and is background `0`; this matches all visible examples and avoids overwriting unrelated cells at a boundary.

Predicted query changes:
- Query 0: cap yellow triples on rows 1 and 4; leave yellow lengths four/five and the `9` triple unchanged.
- Query 1: cap yellow triples on rows 7, 8, and 9; leave both yellow length-four runs and the `5` triple unchanged.
