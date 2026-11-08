# Solve notes

## Hypothesis

Color 8 forms impermeable walls. Treat every 4-connected component of cells that are not 8 as one region, even when a missing wall cell connects two rectangular lobes. Collect the distinct nonzero colors inside that entire connected region:

- exactly one distinct color: flood every cell in the region with it;
- zero colors or at least two distinct colors: leave the region unchanged.

## Visible-example checks

- Training example 1 has an upper-left region with two equal 6 markers; it fills, so eligibility is not “exactly one marker.” Its upper-right region containing colors 4 and 1 stays unchanged, so mixed-color regions do not fill.
- Training example 2 has a wall gap joining upper-middle and lower-middle areas. The connected union contains colors 1 and 7 and stays unchanged, while ordinary one-color rooms fill.
- Training example 3 has a wall gap joining the right-hand lobes. Both lobes contain only color 1, so the whole non-rectangular union fills. This establishes connected-component scope rather than per-rectangle scope.

Implemented one revision using four-neighbor flood fill and a distinct-color set. No reference implementation or private label was consulted during this solve episode. Earlier exposure is yes because this solve follows generator review.
