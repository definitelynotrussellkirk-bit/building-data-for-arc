# Post-repair visible-example solve notes

This is an exposed solve: I had already inspected and repaired this task's generator before `prepare`, so earlier rule exposure is **yes**. During this solve I used only `solve/challenge.json`; I did not reopen the generator, Racket rule, reference solutions, or private labels.

## Revision 1 hypothesis

Across all three visible demonstrations:

1. Column 0 is a key. Its first three cells are a permutation of `1,2,3`; all later key-column cells are zero.
2. Removing column 0 leaves a body whose height divides into three equal horizontal bands.
3. The output preserves every body cell exactly, drops the key column, and concatenates the source bands in the key's top-to-bottom order. A key value of `1` selects the top source band, `2` the middle source band, and `3` the bottom source band.

Checks against the demonstrations:
- Demo 1 key `1,3,2` gives top, bottom, middle.
- Demo 2 key `2,3,1` gives middle, bottom, top.
- Demo 3 key `2,1,3` gives middle, top, bottom.

The implementation derives the common band height from the input, validates the key and rectangular shape, slices the three bands, and emits them in keyed order. No color-specific assumption is used.
