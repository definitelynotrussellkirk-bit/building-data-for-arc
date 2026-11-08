# Exposed replay solve notes

This solve was prepared after the final generator repair and is bound to generator
SHA-256 `b93666cd030874e8e91049d9de47be6d539c492d3e8bccad50b1e9c2847e6ae3`.
I had earlier exposure to the task family while reviewing the generator, so the
episode is marked `earlier_exposure=yes`. I did not consult the hidden reference
implementation or private query labels during this replay.

The visible examples again support the same rule: read transform codes from the
nonzero top-header cells in left-to-right order and output colors from the
nonzero left-header cells in top-to-bottom order. Crop and normalize the body
prototype, apply each requested transform, recolor it for each header color,
and tile the color-by-transform cross-product with one-cell zero separators.
The first transformed panel fixes the common panel footprint; later panels are
clipped to that footprint when dimensions differ.
