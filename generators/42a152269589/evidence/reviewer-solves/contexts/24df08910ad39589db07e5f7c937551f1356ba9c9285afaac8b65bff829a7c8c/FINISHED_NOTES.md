# Visible-only solve work log

## Context and boundary

I am a fresh-context solver. My own context received only the public challenge and the instructions for this solve. I read challenge.json, README.md, the initial solution.py stub, and the initial SOLVE_NOTES.md. I have not read generator source, a Racket rule, reference solutions, private query labels, prior agent solutions, or earlier solution explanations. The final declaration uses earlier-exposure=yes conservatively because the coordinating reviewer had earlier source exposure; it does not describe source exposure by this solver.

## Visible observations

There are three labeled training pairs and two unlabeled test inputs. Every training output is a filled 3 by 4 grid and preserves the twelve nonzero input cells by color. Input components are separate monochrome polyominoes. Example 0 combines a square and domino of color 5 into the left block and a singleton and triomino of color 2 into the upper right block. Example 1 rotates a horizontal color-1 bar to vertical beside the color-5 rectangle. Example 2 packs a five-cell piece and a four-cell piece of color 5 with three singletons. Fitting its top bar and lower zigzag requires allowing reflection as well as rotation.

## Revision 1: exact packing with lexicographic orientations

Hypothesis: extract four-connected monochrome components; enumerate rotations and reflections; tile a 3 by 4 board by placing larger pieces first, breaking size ties by color, then trying normalized shapes and positions lexicographically. A Python experiment against all three visible outputs matched examples 0 and 2, but example 1 produced [[5,5,5,3],[5,5,5,3],[1,1,1,3]], whereas its visible target has the color-5 rectangle vertical at the left. This is a genuine orientation-choice failure, not a failure to preserve shapes or counts. I wrote that actual hypothesis into solution.py and am recording a check before changing it.

Remaining uncertainty: the examples do not establish a unique general tiling convention. Fixed output dimensions are inferred from all three visible targets. Private test correctness is unavailable and is not claimed.

## Continuation boundary

A replacement solver continued the same visible-only attempt after the first worker stopped. This solver read only this directory's README.md, challenge.json, solution.py, SOLVE_NOTES.md, summary.json, and the saved attempt-1 report and execution status. The replacement also inspected the packet's outer entrypoint filenames and the official solve CLI help. No generator source, Racket rule, reference solution, other check, private query label, or other solve directory was consulted. The final declaration still uses earlier-exposure=yes because the coordinator had prior rule exposure; reference-consulted=no reflects this solve's boundary.

## Revision 2: prefer orientations spanning the output height

Attempt 1 officially passed 2 of 3 visible pairs with no execution error. Its only mismatch was the rectangle orientation in example 1. In-memory experiments evaluated three ordinary orientation preferences: original orientation first matched examples 0 and 1 but mirrored the minority-cell arrangement in example 2; tallest orientation first matched examples 1 and 2 but misplaced the dominoes in example 0; preferring orientations that span all three output rows, then retaining the lexical tie-break, matched all three visible targets. These experiments did not overwrite the submitted solution and were not additional frozen revisions.

Revision 2 implements the last preference. Component extraction, rotations and reflections, decreasing-size piece ordering, and exhaustive placement remain as in revision 1. This is a visible-example-compatible packing convention, not a uniquely identified rule. The fixed 3-by-4 shape and general placement tie-break remain uncertain beyond the three demonstrations. The genuine failed first revision remains intact in attempts/0001.

The official revision-2 check passed all 3 of 3 visible examples, with execution_status=completed and reported_label=unknown. The final solution hash is 20f4b0d87471e74a631ee1d9d9072dde4f049f3597673ab9212d3b5e35bf46c0. I stopped after resolving the observed mismatch because further private-query correctness cannot be established from the permitted feedback.
