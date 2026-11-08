# Visible-only solve notes — be5d9fa6fec1

## Hypothesis

Treat each maximal consecutive run of identical rows as one group, numbered from
zero. Recolor every nonzero cell in groups 0, 3, 6, ... to 2; keep zeros and all
other groups unchanged.

## Evidence from the displayed demonstrations

- Example 0 starts with two identical `[1,0,0]` rows; both are recolored, so the
  unit is an identical-row run rather than a single row. The next two runs stay
  unchanged, and the fourth run (`[0,8,8]`) is recolored.
- Example 1 has a two-row first run, then singleton second and third runs; the
  fourth run begins at row 4 and is recolored. This contradicts a fixed
  every-third-physical-row interpretation.
- Example 2 repeats the same zero-based phase across a mixture of singleton and
  multirow runs. Both color 1 and color 8 are recolored when their group is
  selected, so foreground color is irrelevant.

## Implementation choices

The scan compares each row with the immediately preceding input row. The group
counter increments only on a change. The output is a copy, and selected groups
replace every nonzero value with 2 while preserving 0.
