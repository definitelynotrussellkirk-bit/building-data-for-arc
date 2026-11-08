# Solve work log

## Exposure declaration

I had already inspected and repaired the assigned generator before this solve, so
this is **not** a blind rule-discovery episode. During this solve I did not reopen
the generator, Racket rule, reference solutions, private labels, or earlier
solution notes. I used only the newly prepared visible examples and my own code.

## Revision 1

### Visible-example hypothesis

The blue cells (`1`) identify columns. For every column containing at least one
blue cell, erase all of that column's existing blue cells and write one blue
cell in the bottom row of the same column. Preserve every non-blue cell exactly,
except that the new bottom blue cell may replace the prior bottom value.

The second training example is the key visible discriminator: three blue cells
stacked in one column become only one bottom blue cell. Therefore this is not
ordinary gravity that preserves object count; it is a column-presence marker.
The first and third examples show several distinct marked columns and preserve
unrelated gray (`5`) cells away from the destinations.

### Implementation and probes

I implemented the rule in two phases: collect the set of columns containing a
`1`, replace all existing `1`s by `0`, then set the bottom cell of every marked
column to `1`. This directly handles repeated blue cells in one column, blue
cells already on the bottom row, and arbitrary rectangular dimensions.

I then ran the official visible-example checker. No alternative revision was
needed. A plausible rejected alternative was "move each blue cell downward by
gravity"; it fails training example 1 because it would preserve three blue
cells rather than collapse them to one column marker.

### Remaining uncertainty

The examples use only colors 0, 1, and 5. The implementation intentionally
preserves every non-1 value, because all visible changes are explained solely by
relocating/collapsing the blue column markers.
