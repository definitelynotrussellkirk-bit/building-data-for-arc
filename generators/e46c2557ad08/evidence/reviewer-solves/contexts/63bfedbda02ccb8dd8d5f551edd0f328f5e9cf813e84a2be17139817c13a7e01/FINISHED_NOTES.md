# Solve work log

## Exposure declaration

Before this solve I had already reviewed the selected generator and its rule-binding
contract, so this is **not blind** and `earlier-exposure` must be `yes`. During the
solve episode itself I used only the public visible examples printed by `prepare`;
I did not reopen the generator, Racket source, reference solution, or private query
labels.

## Revision 1 — connected-component interpretation

The three visible pairs agree on a precise object rule:

- Treat gray (`5`) cells as 4-connected components.
- A component changes to cyan (`8`) exactly when it contains two horizontally
  adjacent cells and nothing else.
- Vertical two-cell components, horizontal runs of length three or four, vertical
  runs of length three, and a 2×2 block stay gray.
- Shape and background remain unchanged.

This object/component formulation is safer than scanning every adjacent horizontal
pair, because pair scanning would incorrectly recolor two cells inside a longer bar
or a 2×2 block. I implemented flood-fill component extraction and recolor only a
size-two component whose two rows are equal. Remaining uncertainty before checking:
none material for the visible domain; all examples use only background 0 and gray 5.
