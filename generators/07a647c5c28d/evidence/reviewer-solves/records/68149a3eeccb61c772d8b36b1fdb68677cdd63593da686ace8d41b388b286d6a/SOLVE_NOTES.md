# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — bounding box of color 6

Earlier exposure: none. Before this blind episode I had not opened task `07a647c5c28d`'s
rule, generator, notes, solutions, audit records, or private labels.

Hypothesis: color 6 is the invariant marker. The output is the smallest axis-aligned
rectangle containing every 6-valued cell, while retaining any other colors that fall
inside that rectangle.

Visible-example checks:
- Example 1: the two 6s span rows 1–3 and columns 10–11; that crop is exactly the
  3×2 output, while the 9s lie outside it.
- Example 2: the 6s span rows 1–4 and columns 1–3; the enclosed 9s remain in the crop,
  while the separate color-2 segment is discarded.
- Example 3: the 6s span rows 7–9 and columns 4–9; the enclosed 8s remain, while the
  distant 9 pair is discarded.

Implementation: locate all 6 cells, compute their min/max row and column, and return
that inclusive slice. I return an empty list for the out-of-domain no-6 case rather
than guessing a different selector. Remaining uncertainty is only whether unseen
instances always contain color 6; all visible examples do and the transformation is
otherwise exact.
