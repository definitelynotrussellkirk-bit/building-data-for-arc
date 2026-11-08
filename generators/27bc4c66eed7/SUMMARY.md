# 27bc4c66eed7 — horizontal-run midpoint extraction

Each maximal non-zero horizontal same-color run is reduced independently to one
same-colored cell on a fresh zero grid.  For a run beginning at column `start`
with length `L`, the output cell is `start + L // 2`; this is the unique center
for odd lengths and the right-middle cell for even lengths.

## Teaching distribution

- 5–7 rows and 7–10 columns.
- 2–5 maximal horizontal runs, with lengths 1–5.
- Runs may share rows and may reuse colors.
- Four of every five ordinary samples match a canonical `(height, width,
  palette-size)` profile.  The fifth deliberately repeats a color across two
  separate runs.
- Every five consecutive examples therefore refute the strongest public-demo
  shortcut: “emit at most one midpoint per color.”

Public exact axes are `grid_h`, `grid_w`, `n_runs`, `color_mode`, and
`run_length` (`0` means a mixed-length scene; `1..5` fixes every run length). Ordinary samples cycle through mixed lengths and fixed lengths 2–5; fixed length 1 remains an explicit diagnostic override but is excluded from defaults because it makes the rule identity-only. A lone monochrome solid 2×2 is deliberately excluded as a visually ambiguous teaching-only case, although the total authority can execute it.
