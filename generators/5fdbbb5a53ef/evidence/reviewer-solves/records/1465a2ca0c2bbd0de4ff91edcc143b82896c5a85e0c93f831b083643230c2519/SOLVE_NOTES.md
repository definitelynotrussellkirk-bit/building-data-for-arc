# Solve notes — 5fdbbb5a53ef

## Revision 1

The input consists of color-9, 5×5 frames. The frames along the highest frame row form a top gallery; the later frames along the leftmost frame column form a left gallery. Each frame contains a one-color shape in its 3×3 interior. The output has one row per left-gallery frame and one column per top-gallery frame.

The visible outputs support a four-way comparison for each left/top pair:

- `8`: same interior shape (allowing rotation) and same color;
- `6`: same shape under rotation, different color;
- `3`: different shape, same color;
- `0`: different shape and different color.

The implementation scans structurally for complete 5×5 color-9 borders rather than assuming fixed offsets or gallery sizes. It normalizes translation and chooses a canonical representation over four rotations before comparing shapes. I expect all three visible examples to match; the two masked queries are deliberately not inspected through any reference source.
