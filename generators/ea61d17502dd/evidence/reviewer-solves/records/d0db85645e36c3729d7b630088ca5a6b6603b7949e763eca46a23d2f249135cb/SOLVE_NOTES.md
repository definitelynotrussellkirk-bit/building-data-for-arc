# Post-repair visible-only solve notes

Earlier rule exposure: yes, from repairing this assigned generator before this required solve. During this solve I read only `solve/challenge.json`; I did not reopen the generator, Racket source, canonical records, reference solutions, or private labels.

## Visible-example hypothesis

Each input contains one dominant horizontal strand and one dominant vertical strand. Each strand has a frequent base color and a rarer marker color occurring twice. The paired horizontal markers give the left/right bounds; the paired vertical markers give the top/bottom bounds.

The output fills that rectangle as a two-thread weave. The crossing input cell chooses the priority:

- If the crossing equals the vertical base, every other output column is a continuous vertical-base column. On the interleaved columns, rows alternate between the vertical marker color and the horizontal base.
- If the crossing equals the horizontal base, every other output row is a continuous horizontal-base row. On the interleaved rows, columns alternate between the vertical marker color and the vertical base.

The alternation starts at the top-left bound with the vertical marker color. The horizontal marker color is structural: it locates the horizontal bounds but does not paint the interior.

## Checks against the three demonstrations

1. Demo 1 has a horizontal-base crossing. Rows alternate between `vertical-marker / vertical-base` stripes and solid horizontal-base rows.
2. Demo 2 has a vertical-base crossing. Columns alternate between the mixed lane and a continuous vertical-base lane.
3. Demo 3 is partial-span and confirms that bounds come from the two marker pairs rather than the grid edge.

## Implementation

Find the unique row and column with the most nonzero cells, infer frequent/rare colors on each, locate marker endpoints, read the crossing to choose priority, and render only the bounded rectangle. No query answer or hidden feedback was consulted.

## Revision 1 failure and correction

The first implementation scored 0/3 visible examples. The root cause was local and reproducible from the visible inputs: when the crossing belongs to the other strand, a strand line contains a third color exactly once. I had incorrectly selected the least-frequent color as that strand's marker, so I selected the alien crossing color instead of the true marker. The corrected inference selects the strand base as the most frequent color and its marker as the unique color occurring exactly twice. The rendering hypothesis is unchanged.
