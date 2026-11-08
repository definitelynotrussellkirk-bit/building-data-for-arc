# Solve work log

## Exposure declaration

Before this solve I had not opened the task's generator, Racket rule, reference
solution, private query labels, audit records, or prior solution notes. I used
only the visible grids printed by `python3 review.py blind prepare` and the
matching public README.

## Revision 1 — periodic vertical continuation plus recoloring

The output keeps each input row's geometry, changes every blue `1` to red `2`,
and increases the height from `h` to `h + floor(h/2)`. The added rows continue
the shortest vertical period already evidenced by repeated input rows:

- example 0 has row period 3 and grows from 6 to 9 rows;
- example 1 has row period 6 and grows from 9 to 13 rows;
- example 2 has row period 4 and grows from 11 to 16 rows.

I implemented the shortest positive period `p < h` satisfying
`row[i] == row[i-p]` for every observed `i >= p`, falling back to `h` if no
shorter period exists. The output row at index `i` is input row `i mod p`, with
`1 -> 2` and all other colors unchanged.

For query 0 the visible prefix is consistent with period 6, so the four added
rows are period rows 3, 4, 5, and 0. Query 1 has period 2, so three alternating
rows are appended. Remaining uncertainty: the examples identify the intended
period from repeated rows, but a very short prefix can in general admit several
future continuations; choosing the shortest period is the simplest rule common
to all visible examples.
