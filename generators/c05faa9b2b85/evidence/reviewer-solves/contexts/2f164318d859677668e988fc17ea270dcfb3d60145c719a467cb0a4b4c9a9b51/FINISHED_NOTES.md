# Solve notes

This is a human work log from the visible examples only. I had earlier rule exposure from repairing this same task, so this is not blind; I did not consult the generator, Racket source, reference solutions, or private labels after preparation.

## Hypothesis

Color 1 is an impermeable wall. Partition all non-1 cells into 4-connected components. For each component, collect the distinct colors greater than 1:

- exactly one distinct marker color: replace every 0 in that component with that color;
- zero or more than one distinct marker color: leave the component unchanged.

The second training example is decisive against “exactly one marker cell”: one chamber contains two 9 cells and is still filled with 9. Its 6/4 chamber is unchanged, showing that the criterion is one **distinct color**, not one cell. The third example confirms that a mixed 4/2 chamber stays unchanged while a two-7 chamber fills.

## Test predictions

- Test 1: both rectangular chambers have one distinct marker, so their zeros fill with 5 and 9.
- Test 2: the two-2 chamber fills with 2; the 8/7 chamber stays unchanged; the one-5 chamber fills with 5.

I implemented the hypothesis directly with a component flood fill and made no speculative fallback rule.
