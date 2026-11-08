# 33eb6312ab78

A 0-background grid has a contiguous blue header run in row 0 and exactly three separate, differently colored body components.  Let n be the number of blue header cells.  Scan body components in row-major order and take the first object with exactly n boundary cells.  Crop to that object's full bounding box, erase its interior cells, and preserve its boundary in the object's original color.  Most generated scenes have one match; every fourth sample has two matches so the canonical find-first tie branch is taught explicitly.

Kind: `per_puzzle`. Imported version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
