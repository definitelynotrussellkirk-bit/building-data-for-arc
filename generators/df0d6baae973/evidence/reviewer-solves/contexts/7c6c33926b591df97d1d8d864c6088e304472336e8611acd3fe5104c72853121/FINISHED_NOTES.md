# Solve work log

## Exposure declaration before solving

I had not opened task `df0d6baae973`'s generator, Racket rule, reference
solutions, private labels, prior notes, or audit records. I used only the public
visible examples produced by `solve_episode.py blind prepare` and local Python.

## Revision 1 — pairwise color-population comparison

### Observations

Each output is a square symmetric matrix whose side length equals the number of
nonzero input colors. The diagonal is always zero. The apparent row/column order
is ascending numerical color value.

For every off-diagonal pair, the output is the color with the larger number of
input cells:

- Train 0 has counts `6:3`, `7:7`, `9:7`. In color order `[6,7,9]`, 7 beats 6,
  9 beats 6, and the 7-vs-9 tie yields zero, exactly matching the output.
- Train 1 has counts `4:2`, `7:7`, so both off-diagonal cells are 7.
- Train 2 has counts `2:6`, `4:4`, `6:5`, yielding pair winners 2, 2, and 6.

### Hypothesis

Collect all nonzero colors, sort them ascending, and construct an `n × n`
comparison matrix. For each unordered pair, put the color with the greater pixel
count into both symmetric cells. Put zero on the diagonal and for tied counts.

### Alternatives considered

- Comparing bounding-box area or connected-component dimensions: rejected because
  raw cell counts alone explain every pair, including the equal-count 7/9 tie in
  Train 0 despite their different shapes.
- Ordering colors by location, size, or first appearance: rejected because the
  visible matrices consistently match ascending numeric color order.
- Comparing individual connected components: all visible colors form one component;
  total per-color population is the simplest supported interpretation.

### Probe and implementation

Before implementation I ran a visible-example assertion harness against the
provided stub and observed the expected `NotImplementedError`. I then implemented
only the rule above and checked all three visible examples through the official
blind-check command.

### Query predictions

- Query 0 counts are `3:4`, `4:5`, `9:6`; predicted output:
  `[[0,4,9],[4,0,9],[9,9,0]]`.
- Query 1 counts are `3:5`, `5:5`, `7:4`; predicted output:
  `[[0,0,3],[0,0,5],[3,5,0]]`.

Remaining uncertainty: an unseen case with repeated disconnected components of a
single color could distinguish total color population from largest-component
area. The visible examples support total population and provide no evidence for
splitting a color into separate objects.
