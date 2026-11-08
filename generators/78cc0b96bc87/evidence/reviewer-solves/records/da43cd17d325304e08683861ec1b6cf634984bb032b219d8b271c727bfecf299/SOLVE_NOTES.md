# Blind solve work log

## Exposure and observations

I read only the assignment/workflow instructions and the prepared visible
examples before this solve. I did not open any generator, Racket rule, canonical
dataset, private query labels, task notes or earlier solution explanation.
An independent assistant was restricted to the same visible challenge for a
cross-check. No reference-derived assistance was requested.

All three visible examples are 9 by 11 on both sides. A complete, single-color
rectangular frame stays fixed, as does the zero exterior. Two interior seeds
expand into alternating colors by both row and column. Example 2 separates the
seeds horizontally and moves them away from the corner; their absolute (r+c)
parities still specify the two fill colors. Examples 0 and 1 rule out a fixed
numeric ordering of the seed colors. The two query inputs use different palettes.

## Revision 1

Hypothesis: locate the complete rectangular border, map the two observed seed
parities to their colors, and fill only the open interior with that checkerboard.
This preserves the border and every exterior cell. The implementation detects
the frame geometrically instead of relying on its color or global frequency.

Alternatives considered: repeated horizontal stripes fail the alternating rows;
starting a fixed color at the top-left fails example 1. These were reasoning
checks, not submitted failed programs. No artificial negative was created.

Command: from packet root, `python3 review.py blind check --intent solve
--note 'Infer framed checkerboard from visible seeds; phase comes from r+c parity.'`.
Visible-check results are recorded by the check tool. Query answers remain
unscored here. Remaining domain uncertainty: examples show a zero background,
one full frame, and seeds for both parities; more general domains are not claimed.
