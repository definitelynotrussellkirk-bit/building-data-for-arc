# Blind solve notes

I used only the visible examples in `solve-blind/README.md`.

## Hypothesis

The nonzero cells form vertical runs of color 3. The output recolors every
maximal vertical run whose height is exactly 2 from color 3 to color 7, while
leaving runs of heights 1, 3, 4, and 5 unchanged.

Evidence:
- Train 0 recolors the two height-2 runs (columns 0 and 6), but not the
  height-1 or height-4 runs.
- Train 1 recolors its height-2 run and leaves its height-3 run.
- Train 2 recolors both height-2 runs and leaves the height-4 and height-5 runs.

The implementation scans each column for maximal contiguous runs of 3s and
recolors exactly those of length 2. This predicts two recolored runs in query 0
(columns 4 and 0) and one in query 1 (column 6).
