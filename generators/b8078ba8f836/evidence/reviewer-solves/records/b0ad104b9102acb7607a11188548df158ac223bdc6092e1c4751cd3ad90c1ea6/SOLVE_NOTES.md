# Post-repair visible-only solve notes

Earlier rule exposure exists from the generator review, so this is not a blind inference record. During this solve phase I used only the displayed challenge examples and did not reopen the generator, Racket rule, canonical ledger, or private labels.

Visible examples support the following rule:

1. Group all nonzero cells by color.
2. Only a color occurring exactly twice is eligible.
3. If its two cells share a row, fill the inclusive horizontal interval.
4. If they share a column, fill the inclusive vertical interval.
5. Leave diagonal pairs, singleton colors, and colors occurring three times unchanged.

The second and third demonstrations are especially diagnostic: color 9/3 occurs three times and stays unchanged, while exact-two aligned colors are completed. Query 1 contains the same negative controls, so the implementation explicitly tests the exact count rather than merely searching for any aligned subpair.

The solver returns a fresh grid and handles every eligible color independently.
