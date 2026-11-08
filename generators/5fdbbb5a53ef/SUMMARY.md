# 5fdbbb5a53ef

0-bg grid (size varies). Color-9 (maroon) 5x5 FRAMES form an L: a TOP gallery of N frames sharing the top row, and a LEFT gallery of M frames sharing the left column (below the top). Each frame's 3x3 interior holds a shape (a rotation class + orientation) in a color. Rule: output an M x N matrix where cell = 8 if left[r] and top[c] match under rotation AND share a color, 6 if only same-shape, 3 if only same-color, else 0. The grid size, gallery sizes, shapes and colors all vary freely (was a fixed 5-frame layout, ~12 distinct).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
