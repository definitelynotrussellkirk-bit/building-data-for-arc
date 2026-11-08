# Solve notes — 71e2e99645f4

This is a human work log based on the visible examples shown by `solve prepare`.

The 4×14 input splits at the all-zero columns 4 and 9 into three independent 4×4 panels. Each output row corresponds left-to-right to one panel and repeats a class color three times. Comparing visible panels gives four signatures:

- no zero holes inside the panel → 2;
- the central 2×2 cells are zero → 8;
- the lower-middle 2×2 cells are zero → 4;
- the two middle cells on both outer edges are zero → 3.

The nonzero input fill color changes between examples, so it is irrelevant. I implemented exact local-zero signatures rather than position-specific labels. This also explains the two visible queries: query 0 has edge, bottom, none; query 1 has edge, none, center.

No failed revision was needed: the four signatures are jointly present across the three visible demonstrations and the mapping reproduces every visible output.
