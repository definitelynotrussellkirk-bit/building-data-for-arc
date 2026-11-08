# Solve notes

The input always has two colored dots, ordered vertically. Each dot supplies the color and one horizontal edge of a rectangular frame covering its half of the grid.

- The upper dot's color fills the top row, both side columns above the midpoint, and the dot's own row.
- The lower dot's color fills the bottom row, both side columns from the midpoint downward, and the lower dot's own row.
- Example 1 has odd height 15: the color transition starts at row 7, so the midpoint is integer `h // 2`, not a rounded-up half.
- Dot columns do not affect the frame geometry.

This rule explains all three visible demonstrations, including reversed color order and noncanonical dot rows. I implemented it directly without consulting any reference during this solve. I had seen the task rule earlier during generator review, so this is not blind.
