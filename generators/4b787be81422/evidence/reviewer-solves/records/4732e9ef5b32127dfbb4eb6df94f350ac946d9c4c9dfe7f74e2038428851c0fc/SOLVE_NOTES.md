# Visible-only solve notes

The positive examples are invariant under reflection across the vertical axis:
each row reads the same left-to-right and right-to-left. The negative examples
break that property. Other simple features such as foreground count, palette,
shape, and top-bottom symmetry do not explain the labels consistently.

Hypothesis: return `[[1]]` when the whole input is left-right symmetric, meaning
every row equals its reverse; otherwise return `[[7]]`.

The first query satisfies this row-wise mirror condition. The second query does
not. The implementation checks the condition directly and does not depend on
size or foreground color.

Earlier rule exposure existed before this solve episode because the main review
required source inspection. During this solve I used only the visible examples
in `solve/README.md` / `solve/challenge.json`; I did not consult generator,
reference-rule, private-label, or prior-solve material.
