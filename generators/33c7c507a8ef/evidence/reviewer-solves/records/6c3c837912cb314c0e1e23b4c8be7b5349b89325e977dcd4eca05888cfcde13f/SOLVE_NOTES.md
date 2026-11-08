# Visible-examples-only solve work log

## Access boundary and prior exposure

I am the fresh-context solver dispatched for this episode. My puzzle
evidence consists only of `solve/README.md` and `solve/challenge.json`,
plus my own Python experiments on those visible grids. I have not read
the generator, canonical/reference/Racket source, private labels,
private review material, prior solve files, other agents' notes, or
earlier solution explanations.

The overall reviewer had earlier rule exposure during repair. That is
distinct from my own fresh puzzle context. The requested final
declaration therefore conservatively uses `--earlier-exposure yes`
and `--reference-consulted no`.

The challenge contains seven visible input/output demonstrations and
two query inputs. Neither query has an output field. Private query
correctness is not available to me.

## Initial observations and hypothesis

Every demonstration has a marker at the top-left cell, a gray
(color 5) rectangular frame, and a payload inside the frame. The output
contains the interior only. Gray cells that occur inside the frame are
part of the payload and must be retained, as demonstrated by examples
1, 2, and 4. The marker is also a possible payload color, so its color
must not be removed from the interior.

The first hypothesis was to crop one cell inside the bounding box of
all gray cells, then use the corner marker to choose a clockwise
rotation:

| Marker | Clockwise quarter-turns | Interpretation |
| --- | ---: | --- |
| 1 | 0 | Keep the interior unchanged |
| 2 | 1 | Rotate 90 degrees clockwise |
| 3 | 2 | Rotate 180 degrees |
| 4 | 3 | Rotate 90 degrees counterclockwise |

This hypothesis was suggested by direct comparisons of the visible
grids. For example, example 1 has interior `[[5, 5, 0], [0, 5, 9]]`;
one clockwise turn produces its shown `[[0, 5], [5, 5], [9, 0]]`.

## Python experiment before implementation

I loaded only `solve/challenge.json`. For every visible demonstration,
the experiment found the minimum and maximum row and column containing
gray, verified that the bounding rectangle's border was entirely gray,
and extracted its strict interior. It compared all four rotations of
the interior and all four rotations of its horizontal reflection to
the supplied visible output.

| Example | Marker | Frame bounds: top, left, bottom, right | Interior shape | Unique matching clockwise turns | Reflection |
| --- | ---: | --- | --- | ---: | --- |
| 0 | 1 | 3, 3, 8, 9 | 4 by 5 | 0 | No |
| 1 | 2 | 1, 1, 4, 5 | 2 by 3 | 1 | No |
| 2 | 3 | 1, 1, 4, 5 | 2 by 3 | 2 | No |
| 3 | 4 | 1, 1, 4, 5 | 2 by 3 | 3 | No |
| 4 | 1 | 2, 3, 7, 9 | 4 by 5 | 0 | No |
| 5 | 2 | 3, 3, 8, 9 | 4 by 5 | 1 | No |
| 6 | 3 | 1, 1, 4, 5 | 2 by 3 | 2 | No |

All seven borders passed the solid-gray check. Every example had one
matching transform out of eight. Those results supported the initial
hypothesis without a revision.

## Implementation and revision history

Revision 1 is the first actual solver implementation. `solve(grid)`
locates the bounding box of color 5, copies its strict interior, and
applies `grid[0][0] - 1` clockwise quarter-turns. It uses the same general
procedure for every grid and contains no example or query lookup table.
It preserves payload colors and returns fresh lists without changing
the input.

There have been no rejected solver hypotheses or failed solver
implementations at this point. I have not added an intentionally wrong
revision to manufacture a failure history.

## Official verification plan and stopping criterion

Run the supplied checker with `--intent solve` and a note explaining the
crop-and-rotation hypothesis. The checker records execution and the
seven visible comparisons while withholding private query correctness.
Stop if the implemented rule matches all seven visible outputs and
executes on both masked query inputs; finish with the conservative
earlier-exposure declaration above. The checker summary, rather than
any prediction in this log, is the authority for those recorded results.

The inference assumes the shown input format: the top-left cell is the
rotation marker and gray cells outside the payload belong to its frame.
No evidence in the allowed inputs requires other formats. Even a clean
visible result cannot establish private query correctness.
