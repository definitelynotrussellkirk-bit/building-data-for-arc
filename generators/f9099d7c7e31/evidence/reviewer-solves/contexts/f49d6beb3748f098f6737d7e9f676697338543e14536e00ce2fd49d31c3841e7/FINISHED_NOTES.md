# Visible-only solve work log

Task: f9099d7c7e31. This is an authored experimental work log, not a token-level transcript.
Earlier rule exposure: no. No generator, rule, canonical helper, reference solution,
private label or audit was consulted before this attempt.

## Observations and hypothesis

All four visible inputs are 10 rows by 10 columns; their outputs are 3 rows by
5 columns. Examples 0 and 3 crop the purple L. Example 1 crops the blue L while
preserving the green pixels inside that rectangle. Example 2 selects the yellow
object even though the red object has more cells and the cyan object's bounding
box has greater area. Those comparisons rule out simple largest-cell-count and
largest-bounding-box choices on the visible data.

The candidate rule is to find the monochrome connected object whose bounding box
is exactly three rows by five columns, then crop that rectangle from the original
input, preserving any other colors in it. Component size, placement, orientation
and color are not selection criteria. The shape need not be an L: example 2 is
filled more densely.

## Revision 1

Implemented a four-neighbor monochrome component search with a unique 3 by 5
bounding-box requirement. A missing or ambiguous candidate raises an error rather
than inventing a fallback. The four visible examples distinguish size selection
from cell-count/area selection, but do not prove this rule against every possible
hypothesis. Two masked queries are submitted; their reference answers remain
unknown. No deliberately wrong revisions were manufactured.

## Observed check and stopping point

The official visible-only checker completed and matched 4/4 demonstrations on
revision 1. This is the only submitted revision. Both query results were executed
without a reported execution failure; correctness is withheld for maintainer
scoring. Stop because the rule explains every visible example and there is no
observed mismatch to justify another revision.
