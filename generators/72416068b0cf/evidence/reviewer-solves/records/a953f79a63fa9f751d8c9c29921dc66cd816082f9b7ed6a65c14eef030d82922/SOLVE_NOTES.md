# Solve work log

This is a human-authored work log. I had already inspected this task's generator and Racket rule during the repair, so earlier rule exposure is **yes**. During this solve episode I kept those files closed and used only the newly prepared visible challenge.

## Revision 1

The first row behaves as a three-cell instruction header `(shape code, step 1, step 2)`; the remaining rows contain separated monochrome objects. Across the four demonstrations, shape codes select these exact normalized masks:

- code 1: a four-cell L, `10/10/11`;
- code 2: a four-cell T, `111/010`;
- code 3: a zig-zag tetromino, `110/011`;
- code 4: a five-cell block shape, `11/11/10`.

After selecting the uniquely matching colored object, the observed complete step pairs produce:

- `(6,5)`: rotate 180 degrees;
- `(5,1)`: identity;
- `(7,2)`: mirror left/right;
- `(3,4)`: rotate 90 degrees clockwise.

The visible examples do not uniquely identify every individual step code, so I deliberately map complete observed pairs rather than inventing an unsupported factorization. Both queries reuse pairs `(6,5)` and `(5,1)`, respectively. The program excludes header row 0, crops each body color, matches its binary mask, retains the object's color, and applies the demonstrated composition.

Expected visible-query predictions from this hypothesis are a 180-degree-rotated color-4 L for query 0 and the unchanged color-9 T for query 1. Remaining uncertainty is limited to whether private scoring expects generalization to unseen header pairs; this prepared episode contains no such query.
