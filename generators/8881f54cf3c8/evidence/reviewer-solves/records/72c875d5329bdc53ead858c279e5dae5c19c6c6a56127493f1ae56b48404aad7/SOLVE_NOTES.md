# Solve work log

## Exposure declaration

Before this solve phase I had already reviewed and repaired this task's generator and had seen its selected rule semantics. This is therefore an **exposed post-repair solve**, not a blind solve. During this solve phase I consulted only `solve/challenge.json` and my own Python; I did not reopen the generator, Racket source, canonical data, private labels, or a reference solution.

## Revision 1 hypothesis

The top-left nonzero cell is an operation key. The remaining color-2 and color-3 cells form two objects at unrelated absolute positions, so each object must be translated to its own top-left origin before comparing cells.

The four visible demonstrations identify the operations:

- key 1: union of the normalized shapes;
- key 2: intersection;
- key 3: symmetric difference;
- key 4: color-2 shape minus color-3 shape.

The key cell must be excluded from the color-2 object: otherwise the key-2 demonstration would create a huge A bounding box and could not yield the shown compact intersection. The key-3 demonstration is different: its 4×13 output preserves a long separation between a component near the key and the remote color-3 motif, which indicates that every color-3 cell, including the key at `(0,0)`, participates in B. I implemented exactly that asymmetry.

Output dimensions are the maximum normalized bounding-box height and width of A and B, with result cells painted color 4 and all other cells 0.

Remaining uncertainty before checking: none about the four visible examples; the unusual key-3 participation is the only nonstandard detail and is directly visible in the third demonstration.
