# Visible-example solve notes

Earlier rule exposure: **yes**. I had already reviewed the selected generator and
canonical task while repairing it. During this solve phase I read only
`solve/challenge.json`; I did not consult the generator, Racket source, reference
solutions, private labels, or earlier solution explanations.

Across the three visible demonstrations, only blue (`1`) components change, and
changed cells become green (`3`). A solid connected `3×3` blue square changes.
The visible counterexamples distinguish several weaker hypotheses:

- a blue `2×2`, line, L-like component, hollow `3×3`, and larger/tailed blue
  component stay blue;
- a nonblue solid `3×3` stays its original color;
- therefore neither area alone, bounding box alone, containing a `3×3`, nor
  color-agnostic square detection explains the outputs.

Hypothesis: find each four-connected blue component; recolor it only when it has
exactly 9 cells and a `3×3` bounding box. The implementation copies the input,
uses standard-library flood fill, and validates rectangular grids. I stopped
once one implementation matched all visible examples and executed on both public
queries. Masked-query correctness remains withheld by the checker.
