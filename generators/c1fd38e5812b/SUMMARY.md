# c1fd38e5812b

The canonical rule removes consecutive duplicate whole rows and then consecutive duplicate whole columns. The production input grammar expands a smaller color grid with visible first-row and first-column run boundaries, on which boundary sampling gives the same result.

The separate `workspace/parametric/` prototype preserves the exact canonical program as `view=compressed`. Its alternative `view=largest_component_crop` compresses first, selects the largest four-connected monochrome component by logical cell count (including color zero), and crops the original logical grid to that component's bounding box. Ties use lexicographic bounding-box order. This proposed family does not change production approval or admit training data.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
