# c8138b7e476c

Version `3.0.0`; pinned canonical rule hash `df62a46d5c10`.

An odd-height zero-background grid has one centered full row of color 9. The
upper half contains 4–12 cells in 2–4 colors from 1..8; the lower half is blank.
The output preserves the source and separator and reflects the complete upper
half vertically into the lower half, reversing row order while preserving
columns and colors.

Exact controls are `grid_h=7|9|11|13`, `grid_w=7..12`, `cells=4..12`, and
`n_colors=2..4`. Ordinary sampling mixes three canonical-linked profiles with a
broader lawful distribution. Every generated input contains a vertical-order
witness that distinguishes reflection from copying the source rows downward in
their original order.

The task-local semantic contract includes an independent Python oracle, the
`copy_top_in_order` rival, a linked witness, and lesson-level identifiability.
No Racket authority change was made in this review.
