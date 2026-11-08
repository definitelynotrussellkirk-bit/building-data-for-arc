# Blind solve notes — 11221f58af4b

## Hypothesis

The four corners contain marker colors. Across the visible examples, one non-zero
corner color is repeated (three times in the first three examples; twice when the
other two corners are zero). That repeated color is the payload color.

Color 3 draws one or more closed hollow frames. The transformation preserves all
existing cells and fills each zero-valued region enclosed by those frames with the
payload color. I implement this as exterior flood fill rather than rectangle
recognition so all visibly equivalent closed frames are handled without relying on
a particular width, height, count, or placement.

## Checks considered

- Example 1: corners select 1; both framed interiors become 1.
- Examples 2–4: corners select 8; every enclosed interior becomes 8.
- Test 1 should select 1 despite the distinct bottom-right 7.
- Test 2 should select 5 despite the distinct top-right 4.

No reference rule, generator, private labels, prior solution, or task-specific
notes were consulted.
