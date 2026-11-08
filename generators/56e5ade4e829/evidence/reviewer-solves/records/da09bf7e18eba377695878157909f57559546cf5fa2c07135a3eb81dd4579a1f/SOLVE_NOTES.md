# Solve work log

## Exposure declaration before solving

I had not opened the task's generator, Racket rule, reference solution, private
query labels, audit records, or prior solution explanations. I used only the
visible presentation produced by `python3 review.py blind prepare`, the generated
`challenge.json`, and local Python checks against its labelled training pairs.

## Revision 1 — normalized Boolean composition

The input consistently contains one object in color 1, one object in color 2,
and one singleton marker in another color. I cropped each object to its own
bounding box, converted it to a binary mask, aligned both masks at their top-left
corners, and padded them to the larger height and width.

The labelled pairs support these marker operations:

- marker 3: intersection (`A and B`)
- marker 4: union (`A or B`)
- marker 7: symmetric difference (`A xor B`)
- marker 8: directed difference (`A and not B`)

After the operation, occupied cells become color 8 and empty cells become 0. I
trim all-empty outer rows and columns. The marker-8 example alone cannot separate
directed difference from XOR, but marker 7 already identifies XOR, so directed
difference is the least redundant interpretation and exactly fits that example.

I first wrote a local test that imports `solution.py` and compares all five
visible training outputs. It failed with the template's `NotImplementedError`,
then passed after implementing the rule. No query answer or reference source was
consulted.

## Query predictions retained in the program

For the first query, marker 3 leaves one overlapping cell after alignment, so the
program returns a 1×1 color-8 grid. For the second query, marker 4 returns the
trimmed union of the two aligned masks, a 3×3 grid.

Remaining uncertainty is limited to the semantic name/order of marker 8; its
visible output is reproduced exactly, and neither test query uses marker 8.
