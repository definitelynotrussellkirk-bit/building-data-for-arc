# Solve work log

I had no earlier exposure to task `881173b7bc9d`, its generator, canonical rule,
private labels, or prior solution notes. I used only the prepared visible examples
and my own local Python tests.

## Initial observations

Each input contains several nonzero monochrome rectangular outlines. The output
contains no outline colors; instead, it preserves the cells strictly inside some
outlines. The retained interiors are top-aligned, ordered by the outline's left
edge, and separated by one zero column.

The apparent omissions in training examples 2 and 3 are not arbitrary decoys:
those shapes are incomplete frames. In example 2 the color-1 rectangle's lower
border is overwritten/broken where the color-5 frame begins. In example 3 the
color-5 shape has non-5 cells in its would-be lower edge. Every complete frame is
retained, including differently colored and differently sized frames.

## Hypothesis implemented

1. Enumerate axis-aligned rectangles at least 3×3 whose entire perimeter is one
   nonzero color.
2. Discard incomplete/open outlines automatically because they fail the perimeter
   test.
3. Sort complete frames by left coordinate (top coordinate as a tie-breaker).
4. Crop each strict interior.
5. Concatenate interiors left-to-right with one all-zero separator column,
   top-aligning shorter interiors and zero-padding below them.

## Probe and revision record

I first wrote `test_visible_solution.py`, which loads all four visible training
pairs and calls the unimplemented solver. It failed on all four examples with the
expected `NotImplementedError`, establishing a red test before implementation.

A small visible-only enumeration probe found exactly 2, 3, 4, and 2 complete
frames in training examples 0–3 respectively. Those are precisely the components
represented in their outputs; the two suspected decoys produced no complete-frame
candidate. I then implemented the perimeter detector and packing rule.

Remaining uncertainty: no visible example contains two complete frames with the
same left edge. I use top-to-bottom as a deterministic tie-breaker. The examples
also consistently use zero as both canvas background and separator.
