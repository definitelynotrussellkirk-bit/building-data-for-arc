# Solve work log

## Prior exposure

Before this blind attempt I had opened only the packet-level instructions and the
visible examples produced by `review.py blind prepare`. I did not open this task's
generator, rule, notes, reference solutions, private labels, or audit records.

## Hypothesis and probes

The cells colored 4 and 7 are unchanged in every training pair and appear to be
structural. For every other color, the output consistently substitutes the next
larger *present* non-structural color, wrapping the largest color to the smallest:

- example 0: `0 -> 1 -> 5 -> 0`;
- example 1: `3 <-> 6`;
- example 2: `0 -> 3 -> 6 -> 0`.

I also considered rotating labels by frequency or by connected spatial region.
Those descriptions happen to fit the three training examples, but the first test
query contains two colors with the same count and four colors spread across
several disconnected components. Numeric successor order is the single simple
rule that remains unambiguous there and exactly explains every training cell.

I first ran a local visible-training harness against the untouched template and
observed the expected `NotImplementedError`. I then implemented the numeric color
cycle while preserving 4 and 7 and returning a copy for the degenerate zero/one
movable-color case.

## Remaining uncertainty

The examples strongly identify colors 4 and 7 as fixed structural colors. The
main residual uncertainty is whether the intended ordering is explicitly numeric
or encoded by another equivalent property on the training set; test query 0 was
apparently designed to break the frequency-order alternative.
