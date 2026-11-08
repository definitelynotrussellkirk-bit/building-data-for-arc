# Solve work log

## Isolation / prior exposure

This episode was prepared only after I had already reviewed the assigned
generator and its selected Racket rule. I therefore must report
`earlier-exposure=yes`. During this solve I used only `README.md` and
`challenge.json`; I did not reopen the generator, Racket rule, reference
solutions, hidden labels, or earlier solution notes, so
`reference-consulted=no` for the episode itself.

## Hypothesis from visible examples

Each input has one unique vertical column whose cells are all the same
non-zero color. Treat that column as a mirror/divider. For every other
non-zero cell at `(row, col)`, retain the original and copy its color to
`(row, 2*divider-col)` when that reflected coordinate is in bounds.

Evidence across the four demonstrations:

- Example 0 reflects a left-side color-4 shape across column 4.
- Example 1 reflects a right-adjacent color-2 shape across column 2.
- Examples 2 and 3 show that every foreground color is mirrored independently,
  including singleton minority colors; color frequency is irrelevant.
- The divider itself is unchanged, and the output shape is unchanged.

The implementation locates the divider structurally rather than assuming a
specific color or side. It copies from an immutable view of the input so a
newly reflected cell cannot trigger a second edit.

## Remaining uncertainty

The examples do not show foreground collisions at reflected positions or a
shape extending beyond the grid. The generated instances appear constructed so
all reflections are in bounds and compatible; the implementation nevertheless
bounds-checks each reflection. If a reflected location were already occupied,
the mirrored source color would overwrite it, matching the direct reflection
interpretation.
