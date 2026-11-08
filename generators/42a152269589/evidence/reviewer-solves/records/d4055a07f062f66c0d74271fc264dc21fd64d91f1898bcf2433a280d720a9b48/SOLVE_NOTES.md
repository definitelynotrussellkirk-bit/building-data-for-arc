# Visible-only solve work log

## Context and boundary

I am a fresh-context solver. My own context received only the public challenge and the instructions for this solve. I read challenge.json, README.md, the initial solution.py stub, and the initial SOLVE_NOTES.md. I have not read generator source, a Racket rule, reference solutions, private query labels, prior agent solutions, or earlier solution explanations. The final declaration uses earlier-exposure=yes conservatively because the coordinating reviewer had earlier source exposure; it does not describe source exposure by this solver.

## Visible observations

There are three labeled training pairs and two unlabeled test inputs. Every training output is a filled 3 by 4 grid and preserves the twelve nonzero input cells by color. Input components are separate monochrome polyominoes. Example 0 combines a square and domino of color 5 into the left block and a singleton and triomino of color 2 into the upper right block. Example 1 rotates a horizontal color-1 bar to vertical beside the color-5 rectangle. Example 2 packs a five-cell piece and a four-cell piece of color 5 with three singletons. Fitting its top bar and lower zigzag requires allowing reflection as well as rotation.

## Revision 1: exact packing with lexicographic orientations

Hypothesis: extract four-connected monochrome components; enumerate rotations and reflections; tile a 3 by 4 board by placing larger pieces first, breaking size ties by color, then trying normalized shapes and positions lexicographically. A Python experiment against all three visible outputs matched examples 0 and 2, but example 1 produced [[5,5,5,3],[5,5,5,3],[1,1,1,3]], whereas its visible target has the color-5 rectangle vertical at the left. This is a genuine orientation-choice failure, not a failure to preserve shapes or counts. I wrote that actual hypothesis into solution.py and am recording a check before changing it.

Remaining uncertainty: the examples do not establish a unique general tiling convention. Fixed output dimensions are inferred from all three visible targets. Private test correctness is unavailable and is not claimed.
