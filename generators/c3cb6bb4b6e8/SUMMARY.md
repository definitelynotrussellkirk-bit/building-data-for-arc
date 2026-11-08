# c3cb6bb4b6e8

Extract and remove the unique blue (1) template. For every gray connected component that is itself a hollow rectangular frame, read its local key: 2 keeps the template, 3 rotates it 90 degrees clockwise, 4 rotates it 180 degrees, and 5 rotates it 90 degrees counter-clockwise. Center the transformed copy in that frame's 5x5 interior and recolor it to the key color. Preserve all frames and keys. Touching frame borders merge into a non-frame component, so the selected oracle preserves that group without adding copies.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
