# Solve notes

The two full-height color-5 columns divide each 14-column input into three aligned 4-column panels. Comparing the visible examples cell-by-cell shows that the output is 8 exactly when at least two of the three aligned panel cells are nonzero; one-panel cells are omitted and two- or three-panel cells are kept. The output has the same height as the panels and width 4.

The implementation parses the fixed panel starts (0, 5, 10), counts occupancy at each local coordinate, and emits 8 for counts at least two, otherwise 0. No reference source was consulted during this solve. I had already seen the rule while reviewing the generator, so earlier exposure is yes.
