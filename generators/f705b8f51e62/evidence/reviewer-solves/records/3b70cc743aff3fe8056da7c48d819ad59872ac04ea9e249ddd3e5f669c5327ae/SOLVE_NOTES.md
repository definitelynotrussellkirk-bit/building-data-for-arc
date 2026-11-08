# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — repeated-shape extraction

Earlier rule exposure: none. I used only the visible examples in this solve packet.

Hypothesis: split the nonzero cells into separated 4-connected objects and compare
their tightly cropped binary masks, ignoring color. One shape occurs repeatedly;
the other, singleton shape is a color key. The output is one cropped copy of the
repeated shape painted with the singleton object's color. When all objects share a
color, this naturally preserves that color.

Evidence from the visible examples:
- Example 0 has four identical five-cell masks in color 9 and one three-cell mask
  in color 4; the output is the repeated five-cell mask in color 4.
- Example 1 has two identical four-cell masks and one different three-cell mask,
  all color 1; the output is the repeated mask in color 1.
- Example 2 again has four identical seven-cell masks in color 9 and one different
  five-cell mask in color 4; the output is the repeated mask in color 4.

Implementation: enumerate 4-connected nonzero components, normalize each to a
binary bounding-box mask, choose the most frequent mask, and paint it with the
first component outside that repeated group. Remaining uncertainty is limited to
ties or multi-colored touching objects, neither of which appears in the visible
examples.
