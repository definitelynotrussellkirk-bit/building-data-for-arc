# dcfb4c64c914

A centered full-height gray(5) divider separates two panels. Each panel contains one independently positioned monochrome 4-connected object. For each object, crop conceptually to its own bounding box and count object cells on every local row. Pad the shorter row-profile list with zeros, take elementwise absolute differences, and render the resulting list as a left-justified cyan(8) histogram.

The generator includes vertically staggered objects so profiles cannot be aligned by absolute canvas row, and internally gapped rows so horizontal span cannot substitute for cell count. Its five exact observable axes are layout, profile relation, row geometry, vertical alignment, and ordered color pair.

Kind: `per_puzzle`. Generator version: `3.0.0`. Rule hash: `53fe6f709bdc`.
