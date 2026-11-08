# Visible-only solve notes

## Observation

Across all three training examples, repeated nonzero cells of the same color in one row become a solid horizontal segment between their leftmost and rightmost positions. Rows are independent. A color that occurs only once in a row is unchanged, including the unrelated singleton colors in training example 2.

## Rule used

For each row and each nonzero color appearing at least twice in that row, fill every cell from its leftmost occurrence through its rightmost occurrence with that color. Leave all other cells unchanged.

## Integrity declaration

- Earlier exposure to the rule/task: **yes**. I had already inspected and repaired this assigned generator before this required post-repair solve.
- Reference, generator source, canonical labels, or rule implementation consulted during this solve episode: **no**.
- The solution above was written from the visible training pairs in `challenge.json` only.
