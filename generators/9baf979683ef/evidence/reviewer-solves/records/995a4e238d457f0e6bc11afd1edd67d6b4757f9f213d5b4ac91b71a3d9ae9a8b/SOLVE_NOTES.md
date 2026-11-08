# Visible-only solve work log

This is an exposed post-repair solve: I had already reviewed the task rule before
preparation, so earlier exposure will be declared **yes**. During this solve I
consulted only `solve/challenge.json` and did not reopen the generator, Racket
rule, canonical ledger, or reference outputs.

## Hypothesis 1

Each training input has one full-height column of colour 5. Every nonzero cell
left of that divider remains in place and is copied to the same row on the right
at equal horizontal distance from the divider. Colour 5 is the reflection axis,
not a source object. Background stays 0.

Checks against the visible pairs:

- In train 1, divider column 7 maps source column 6 to 8, 5 to 9, 4 to 10,
  3 to 11, and 2 to 12; every shown output addition follows that map.
- In train 2, divider column 3 maps columns 2, 1, 0 to 4, 5, 6.
- In train 3, divider column 7 again maps columns 6, 4, 3 to 8, 10, 11.

The same single rule explains all visible additions and preserves all inputs, so
I implemented it directly and stopped after one checked revision if all visible
examples passed.
