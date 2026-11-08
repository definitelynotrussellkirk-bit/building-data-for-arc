# Solve work log

This is a human work log. I had already inspected the assigned generator and its rule during the repair, so this episode is **not blind**; I deliberately kept those sources, prior solution notes, and private labels closed after `prepare`. The hypothesis below was checked only against `solve/challenge.json`.

## Revision 1

The output is always a 2×3 row-major tally. Count each maximal horizontal run of color 3, then each maximal horizontal run of color 2. Write one `3` per color-3 run followed by one `2` per color-2 run, truncate after six cells, and pad unused cells with 0.

Visible evidence:

- Training 1 has three horizontal 3-runs and three horizontal 2-runs, producing `333/222`.
- Training 2 has five horizontal 3-runs and three horizontal 2-runs; the six-cell output is `333/332`, so overflow is truncated after the first 2.
- Training 3 has two horizontal 3-runs and three horizontal 2-runs, producing `332/220`.

The examples also distinguish two tempting alternatives. Counting 4-connected components is wrong because vertically adjacent same-color runs remain separate tally units. Counting occupied rows is wrong because two separated runs of the same color in one row contribute two units. No deliberate negative was manufactured; the first visible-example hypothesis fits all three demonstrations.

Remaining uncertainty is limited to the masked query labels, which the checker intentionally withholds.
