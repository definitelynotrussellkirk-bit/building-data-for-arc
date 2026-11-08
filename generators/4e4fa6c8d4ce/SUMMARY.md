# 4e4fa6c8d4ce

A large block mask in the uniquely most-common nonzero color controls a separate
3×3 or 4×4 palette. The output copies each palette cell exactly when the
corresponding large block is present and writes `0` otherwise.

Version `3.0.0` uses a four-slot canonical curriculum:

- `27×25×9`: connected 3×3 mask, seven non-shape palette colors;
- `27×21×9`: disconnected 3×3 mask with a filled shape-color palette cell;
- `22×22×10`: disconnected 4×4 mask with a filled shape-color palette cell;
- `21×24×10`: connected 4×4 mask with all eight non-shape palette colors.

Every sliding three-demonstration window refutes the named rivals, including the
canonical-only shortcut that suppresses shape-colored output cells. All six
published axes are observable and round-trip through `observe_overrides`.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
