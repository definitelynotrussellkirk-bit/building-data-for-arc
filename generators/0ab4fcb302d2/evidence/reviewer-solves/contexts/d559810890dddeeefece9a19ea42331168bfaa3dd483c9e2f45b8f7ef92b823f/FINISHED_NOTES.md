# Solve work log

## Exposure declaration

Before this visible-only phase I had already reviewed the assigned generator and
canonical rule as required by the repair lane, so this is **not blind** and
`earlier_rule_exposure=yes` is required. During this solve I did not reopen the
Racket rule, generator implementation, reference solutions, private labels, or
prior solution explanations. I used only the displayed examples and this Python
implementation.

## Revision 1 — coded gaps and marker-selected diagonal

All three inputs are 3x3 with exactly one all-zero row and one all-zero column.
Removing those gaps leaves a 2x2 code containing one red `2` and three copies of
the output color. The corresponding input gap index 0/1/2 becomes output gutter
index 0/4/8, while each non-gap row and column expands to four cells.

The red marker selects which two expanded quadrants are painted. In examples 1
and 2 it lies on the local 2x2 main diagonal and the two output blocks are on the
main diagonal. In example 0 it lies off that diagonal and the two output blocks
are on the anti-diagonal. I implemented exactly that relation, with structural
validation and no query-specific constants.

Remaining uncertainty is limited to hypotheses not distinguished by the three
examples; the implementation follows the simplest shared code-and-expansion
rule and preserves both the observed gutter placement and marker role.
