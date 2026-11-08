# Solve work log

I had no earlier exposure to task `c2b9484357c1`, its generator, or its rule. I used only `solve-blind/challenge.json`.

## Revision 1 — largest incomplete component by painted-cell count

Each example contains several monochrome rectangular components. Some are solid rectangles and therefore unchanged; the others contain holes. Exactly one incomplete rectangle is filled to its bounding box.

A bounding-box-area rule fails on the fourth training example: the hollow 9 rectangle has area 24, but the denser 8 rectangle has area 20 and is the one filled. Counting already painted cells resolves all examples:

- train 1: selected 5 has 14 cells; competing 4 has 8;
- train 2: selected 8 has 16; competing incomplete 1 has 11; solid 6 is ignored;
- train 3: selected 2 has 16; competing incomplete 4 has 13; solid 3 is ignored;
- train 4: selected 8 has 18; competing 9 has 16.

The program finds 4-connected same-color components, excludes components whose bounding boxes are already solid, selects the remaining component with the largest painted-cell count, and fills its bounding box. Remaining uncertainty: ties are not demonstrated; Python tuple order supplies a deterministic fallback, but the visible examples do not establish the intended tie rule.
