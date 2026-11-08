# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — row-count difference bars

Earlier rule exposure: none. I only read the visible challenge prepared for this
blind lane.

The input has one full-height color-5 vertical divider. Each side contains one
colored object. Cropping each object to its occupied rows and counting foreground
cells per row gives:

- Example 0: left `[4,2,5,1]`, right `[5,4,2]`; top-aligned absolute
  differences `[1,2,3,1]`, exactly the output bar lengths.
- Example 1: left `[5,2,2,2,1]`, right `[2,1,1,1,1]`; differences
  `[3,1,1,1,0]`, exactly the output.
- Example 2: left `[4,2,4,2]`, right `[5,3,4,4]`; differences
  `[1,1,0,2]`, exactly the output.

Hypothesis: top-align the two cropped row-count sequences, treat missing rows as
zero, take absolute differences, and render each difference as a left-aligned
color-8 bar. Output height is the longer sequence and output width is the largest
difference. The implementation identifies the unique full-height nonzero divider
instead of hard-coding its column.

Predicted query bar lengths are `[4,1,2,1]` and `[0,1,1,1,5]`.
