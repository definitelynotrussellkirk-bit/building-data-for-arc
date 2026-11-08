# Blind visible-only solve work log
This is an assistant-authored work log, not a token-level trace. No generator,
Racket rule, private labels, reference solution or earlier task notes were opened.
Earlier exposure: no known exposure to task a6211f2301a7.

The three visible examples remove the all-zero exterior and rotate the entire
remaining nonzero bounding box clockwise by 90 degrees. Internal zero rows are
preserved: example 2 has a zero column in its output, excluding a compression rule.
Example 1 crop is [[0,0,7],[2,1,0]], whose clockwise rotation equals its output.
Example 3 gives the same orientation; crop-only and counterclockwise rotation
would disagree. These are considered alternatives, not submitted failed solves.

Revision 1 implements this directly with rectangular-grid validation. An empty
foreground returns [[0]] as a conservative unobserved-domain convention. Only
the three visible example outputs will be used to assess the hypothesis.
