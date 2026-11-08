# Solve work log

## Earlier exposure

Before this solve I had already inspected and repaired the assigned generator and had seen the canonical rule during the review workflow. I therefore mark earlier exposure as **yes**. During this solve episode I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solve notes; I used only the newly prepared visible examples.

## Revision 1

**Hypothesis.** Each input contains one full row of color 5 separating two equal-height panels. The output keeps the input and copies every nonzero cell above that divider into the vertically reflected row below it, preserving column and color. Equivalently, for divider row `d`, source `(r,c)` maps to `(2*d-r,c)`.

**Evidence from visible examples.** In the 11-row examples, top row 0 appears at bottom row 10, row 1 at row 9, and row 4 at row 6. In the 9-row example, row 0 appears at row 8 and row 2 at row 6. Blank rows remain blank, and the divider is unchanged. This rules out copying the top rows below in their original order.

**Implementation.** Find the unique row consisting entirely of 5s, deep-copy the input, and write every nonzero top-panel cell to its reflected coordinate. Fail closed if there is not exactly one divider or the reflected row would be out of bounds.

**Remaining uncertainty.** None for the visible grammar; both panel heights shown obey the same coordinate formula.
