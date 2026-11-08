# Post-repair solve work log

## Exposure and evidence boundary

Earlier exposure: **YES**. Before this solve phase I worked on this family's
parametric prototype and saw its transformation and reference source. This
attempt cannot be characterized as an independent blind rediscovery.

Reference consulted during this solve: **NO**. From the start of this phase I
opened only this lane's README, public challenge, solution template and work log.
I kept generator source, prototype source, reference programs, canonical records,
private query labels and previous solution explanations closed. I used fresh
Python experiments on the public demonstration pairs.

## Observations and revision 1

There are three labeled demonstrations and two query inputs. Both query outputs
are absent from the public challenge and remain unknown.

Orange (7) fills the canvas and separates solid bottom-aligned bars. Black (0)
is a bar color. Bar columns and canvas sizes remain fixed. My first experiment
(`python3 -`, loading only `WORK/solve/challenge.json`) extracted each column's
bottom color and non-orange cell count. The visible profiles were:

| Example | Input colors | Output colors | Input heights | Output heights |
| --- | --- | --- | --- | --- |
| 0 | 4,5,0,2 | 2,4,5,0 | 4,2,2,2 | 2,2,2,4 |
| 1 | 5,6,4,0 | 0,5,6,4 | 9,6,9,5 | 6,9,5,9 |
| 2 | 4,1,0,9 | 9,4,1,0 | 6,3,6,3 | 3,6,3,6 |

The colors move one position right while the height list moves one position
left. Heights therefore move independently of colors, rather than remaining
attached to whole bars. Example 2 alone cannot distinguish left from right
height rotation because its heights alternate; examples 0 and 1 resolve this.

A second `python3 -` experiment compared all nine combinations of color and
height offsets in {-1,0,1} against the visible profiles. Positive denoted right.
Only (+1,-1) fitted all three examples; (+1,+1) fitted example 2 only, and the
other seven combinations fitted none. These are actual observed comparisons,
not failed submitted solutions.

I wrote a fresh `solve(grid)` that finds occupied columns, reads their colors
and heights, applies the two list shifts and redraws on a fresh orange canvas.
The solution does not import the prototype or any repository rule. This is the
first submitted implementation; no unsuccessful solve-check attempt has occurred.

## Remaining uncertainty before the checker

The three examples support this rule within the tested local rotation family;
they cannot exclude every arbitrary alternative. Query correctness is withheld
and will not be inferred from successful execution alone.

## Actual checker result and stopping reason

Ran from the outer packet directory:

```sh
python3 review.py solve check --intent solve --note 'Revision 1: visible bar profiles support colors right and heights left; only this offset pair fits all three demonstrations. Earlier prototype exposure is disclosed in SOLVE_NOTES.md; no references were consulted during this solve.'
```

Actual process exit: **0**. Revision 1 execution completed and passed **3/3**
visible demonstrations. The checker reported the correctness label **unknown**;
it did not disclose correctness for either query. No failed check or revision
was needed. I am stopping because the observed demonstrations pass and the
checker offers no query correctness feedback, not because private correctness
has been established. Earlier exposure remains YES and reference consultation
during this solve remains NO.
