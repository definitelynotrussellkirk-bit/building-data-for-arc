# Blind solve work log

## Evidence and exposure

I used only `challenge.json`, its visible-example `README.md`, and my own Python probes. I have no earlier rule exposure and did not consult a generator, reference solution, canonical data, private labels, audit file, or another task's solution. There are four visible training pairs and two unlabeled query inputs.

## Hypothesis and probe

Each input has a blue marker (1), a red shape (2), and a green shape (3). The output is an otherwise empty grid of the same dimensions, with color 8 near the marker. I hypothesized that each source shape is independently translated so that its bounding box starts at (0, 0), combined by a set operation, and then placed with that common origin at the marker. The combined result must retain its original coordinate offsets: in examples 2 and 3, its occupied cells do not start at the marker.

A Python probe extracted the two normalized coordinate sets and compared five operations against all output-8 coordinates relative to the blue marker:

| Operation | Visible pairs matched |
| --- | ---: |
| Symmetric difference (XOR) | 4/4 |
| Union | 0/4 |
| Intersection | 0/4 |
| Red minus green | 0/4 |
| Green minus red | 0/4 |

These were candidate-operation probe results, not failed solver submissions. The XOR target offsets were:

- Example 0: (0,0), (0,1), (1,2), (2,0).
- Example 1: (0,2), (1,1), (2,1).
- Example 2: (2,1), (2,2).
- Example 3: (0,2), (0,3), (1,1), (2,1).

## Solver revision 1

Implemented `solve(grid)` using bounding-box normalization for each color, symmetric difference, and translation to the marker. It retains the input dimensions, clears all original colors, and paints the retained coordinates 8. The implementation uses no training-case lookup or query-specific branch.

The implementation clips any translated coordinate outside the finite grid. All visible examples and queries have room for the normalized shapes, so clipping behavior is an untested convention. Inputs with different color roles, multiple markers, or different shape-alignment rules are outside the evidence. No rotations or reflections are needed by the visible examples.

The prescribed blind check will test this first solver revision. Private query correctness remains unknown and must not be inferred from successful execution.
