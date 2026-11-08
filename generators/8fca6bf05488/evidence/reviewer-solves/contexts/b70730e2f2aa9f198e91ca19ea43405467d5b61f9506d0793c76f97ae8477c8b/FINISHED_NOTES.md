# Solve work log

This is a human work log, not a captured model trace. I had already inspected the
selected generator during the repair, so this episode is intentionally declared
as exposed (`earlier-exposure yes`). During this solve phase I read only the
visible challenge and did not reopen the generator, Racket source, private labels,
or any reference solution.

## Hypothesis

Every nonzero input cell is the start of a vertical ray extending through the
bottom row in the same color. The fourth demonstration shows that equal colors
are independent sources. The second demonstration contains two sources in the
same column (2 above 4): the lower 4 replaces the lower suffix, which is exactly
what row-major source processing produces.

## Implementation

Copy the input, scan original nonzero cells from top to bottom and left to right,
and write each source color from its row through the final row. Reading sources
from the original input avoids treating newly painted cells as new sources.
