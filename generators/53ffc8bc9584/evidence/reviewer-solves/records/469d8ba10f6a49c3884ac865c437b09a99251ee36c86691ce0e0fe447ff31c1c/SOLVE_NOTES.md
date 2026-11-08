# Blind solve notes

Assignment: `review-89effc2f42a416a4`  
Blind task: `53ffc8bc9584`

## Exposure and scope

I read only `WORK/solve-blind/README.md` and
`WORK/solve-blind/challenge.json` as task evidence. I have not read a
generator, Racket rule, canonical data, prior notes, audit evidence,
reference solution, private labels, or masked query outputs. I had no
earlier exposure to the underlying rule. The analysis below uses the four
visible input/output examples and my own Python probe of those examples.

## Observations

All four demonstrations retain their dimensions and every existing nonzero
cell. Each has exactly two changes from 0 to 9.

- Example 0 completes two yellow L shapes into 2-by-2 blocks.
- Example 1 completes one L and the notch of a five-cell yellow U. The
  notch lies in two overlapping 2-by-2 windows, each with three yellow
  cells, so both windows propose the same fill.
- Example 2 completes the two orthogonally joined yellow L shapes while
  leaving the three separated, diagonal yellow cells unchanged.
- Example 3 completes the yellow shapes at the left and bottom/right
  boundaries and leaves an otherwise similar shape in color 8 unchanged.

## Initial hypothesis

Scan every 2-by-2 window of the original input. If it contains exactly
three cells of color 4 and one cell of color 0, change that zero to 9 in a
copy of the input. Leave everything else unchanged. Overlapping windows
can nominate the same cell, which is simply colored once. Reading only
the original grid makes this a simultaneous transformation.

The five-cell U makes an exact-three-cell-component interpretation too
narrow. The color-8 example argues for color 4 specifically, and the
diagonal distractor argues against filling arbitrary three-point shapes.
These are observations from supplied examples, not separately submitted
failed revisions. The examples cannot distinguish every possible broader
rule; the local 2-by-2 condition is a compact rule explaining all changes.

## Probe before implementation

Ran an inline Python script from the packet root that loaded only
`challenge.json`, enumerated the actual changed cells, and independently
enumerated the zero corners of qualifying 2-by-2 windows. The predicted
coordinates matched all observed changes:

| Example | Actual and predicted fill coordinates, zero-based |
| --- | --- |
| 0 | (1, 3), (4, 3) |
| 1 | (4, 1), (7, 6) |
| 2 | (1, 0), (7, 6) |
| 3 | (4, 0), (7, 8) |

All four coordinate comparisons returned `true`. The U notch in example
1 was found by two overlapping windows, as expected. No candidate failure
occurred during this probe.

## Implementation and check log

Revision 1 implements the hypothesis directly in `solution.py`, exporting
`solve(grid)`. It returns a separate list of rows, preserves original
colors, and scans windows that lie completely inside the input.

Next command:

```sh
python3 review.py blind check --intent solve --note 'Initial hypothesis: simultaneously fill the zero corner of every 2x2 window with exactly three 4s; visible coordinate probe matches all four demonstrations, including the U notch and color-8 distractor.'
```

There are no earlier solver revisions or checker results. No failed
attempts have been invented. Masked query correctness is not known and
will not be inferred from visible-example or execution feedback.
