# Visible-only blind solve: b1e8f6552b5f

## Exposure and observations

I read only the prepared public presentation and challenge. Before this attempt
I had not opened any task generator, Racket rule, canonical pair, solution,
notes, or audit evidence. Preparation and checking may execute the private
reference automatically; I did not inspect its source or private outputs.

The four visible examples have matching input/output dimensions: 7 by 7,
9 by 9, 11 by 9, and 13 by 13. Their backgrounds are zero. Every nonzero
input cell becomes the center of an eight-cell, same-color, hollow 3-by-3
square. The input marker itself is erased. The third example includes rings
touching the top, left, and right boundaries, so no extra border is required.

## Hypothesis 1 and implementation

For each nonzero input cell, paint its eight immediate neighbors in its
color, leave the center at background zero, and preserve grid dimensions.
I used a fresh zero grid and read all marker locations from the input.
Bounds checks are a conservative extension; all visible rings fit completely.
There is no visible evidence for a conflict rule for overlapping colors.
The prepared queries also have separated markers and do not need such a rule.

Rejected by inspection, before implementation: a filled 3-by-3 block or a
four-neighbor cross, since both disagree with the first visible output.
These were conceptual alternatives, not submitted failed solution revisions.

I submitted one genuine solve revision to the public checker. I will retain
the actual visible-example result, and do not infer masked-query correctness
from successful execution.
