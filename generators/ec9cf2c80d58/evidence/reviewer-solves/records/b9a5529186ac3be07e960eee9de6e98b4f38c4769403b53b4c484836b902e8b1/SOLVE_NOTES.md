# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — untouched baseline

- Earlier exposure before this solve: none. I read only the packet workflow and the visible challenge prepared for this solve.
- Probe: ran the checker with the untouched `NotImplementedError` stub.
- Result: execution error on all 3 visible examples, as expected. This establishes a failing baseline before implementation.

## Revision 2 — region-local zero-line completion

Visible observations:

- Each nonzero color occupies a rectangular panel; zeros are holes inside one panel.
- In every panel containing zeros, all columns from the leftmost zero through the rightmost zero become zero for the full panel height. This accounts for every singleton and for the three-dot top panel in example 2.
- Example 1's right panel has a vertical adjacent zero pair. In addition to its full zero column, the lower member's entire panel row becomes zero. I model this directly: any original zero with an original zero immediately above it completes its row across that panel.
- Panels without zeros remain unchanged.

Implementation plan: infer each colored panel from that color's bounding box, inspect only original zero cells inside it, apply the column-span completion, then apply the adjacent-pair row completion. Remaining uncertainty: the row rule is inferred from one visible vertical-pair case, but both query shapes contain cases directly covered by the visible patterns.
