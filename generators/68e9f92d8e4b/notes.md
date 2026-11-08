# Working notes: 68e9f92d8e4b

## Production repair

The previous validator connected all orthogonally touching nonzero cells,
regardless of color. It therefore rejected four of five canonical inputs even
though the canonical Racket rule operates on same-color objects. Ordinary draws
also kept every L isolated, allowing a weaker whole-nonzero-component shortcut.
The production source now discovers equal-color components, accepts lawful
cross-color contact and occupied missing corners, and guarantees a cross-color
teaching contact in ordinary generation.

## Native family

The exact canonical program is preserved byte-for-byte as
`fill_mode=object_color`. The alternate `fill_mode=orientation_legend`:

1. discovers each same-color three-cell L and its missing 2x2 corner;
2. derives the corner orientation NW/NE/SW/SE as index 0/1/2/3;
3. consumes that input-derived index to select one of four top-row legend colors;
4. paints the missing cell with the selected color.

Inputs are identical across settings, support 2-6 demonstrations and exactly
four queries, exercise all four orientations, include touching differently
colored objects, and end with a substantive 30x30 query.

## Evidence and limits

- 20 focused staged tests passed, including protected-Racket parity.
- 40 bounded audit episodes rejected four declared shortcuts in every episode.
- The protected wrong-intermediate witness forces all orientation indices to 0
  and changes the final output.
- 16 public one-query projections passed verification; 4 first turns passed 24
  private-field invariance mutations and 4 visible-change controls.

These are reviewer-side authoring checks and finite declared-rival evidence, not
universal uniqueness, owner acceptance, or training admission. Exact-source
owner qualification and fresh acceptance remain required.
