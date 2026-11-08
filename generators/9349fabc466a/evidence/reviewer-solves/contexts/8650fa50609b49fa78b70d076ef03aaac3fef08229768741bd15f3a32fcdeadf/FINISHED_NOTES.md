# Solve work log

## Exposure record

Before this solve I had not opened the generator, Racket rule, reference solution,
private query labels, prior solution explanations, or any audit evidence for task
`9349fabc466a`. I used only the visible examples prepared in this directory.

## Revision 1 — aligned same-color segments

The examples consistently treat each nonzero color independently. Whenever two or
more cells of one color share a row, the output fills the interval between the
extreme cells. The same happens for shared columns. Four cells at two rows and two
columns therefore become a rectangular perimeter; an unpaired marker remains
unchanged. Where the two colors' newly completed lines cross, color 4 remains over
color 5 in every visible example. The test queries rename those roles to colors 1
and 2, so I infer that the lower-numbered structural color has precedence.

I first wrote a visible-example regression test and a synthetic crossing test.
They failed on the untouched `NotImplementedError`, then passed after implementing
`solve`. The implementation copies the input, indexes original nonzero positions,
connects row and column extrema for each color, and draws colors in ascending order
without overwriting an already nonzero cell. This reproduces all three visible
training outputs and does not mutate the input.

Remaining uncertainty: the examples do not show a lower-color segment crossing an
original higher-color marker, so the code conservatively preserves every original
nonzero marker. They also do not prove whether numeric order or semantic role alone
sets crossing precedence, but the 4→1 and 5→2 recoloring strongly supports numeric
order for these queries.
