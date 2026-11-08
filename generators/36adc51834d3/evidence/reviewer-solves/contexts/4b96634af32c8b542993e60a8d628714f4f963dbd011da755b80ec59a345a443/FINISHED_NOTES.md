# Solve work log

## Exposure declaration

This is the required post-repair solve, not a blind solve. Before `prepare` I had already inspected and repaired task `36adc51834d3`, including its generator, canonical pairs, and Racket-rule behavior. I therefore declare earlier rule exposure **yes**. After `prepare`, I used only `solve/challenge.json`, this Python file, and visible check feedback; I did not reopen the generator, Racket rule, references, private labels, or earlier solution explanations.

## Revision 1 — corner command selects a quarter-turn

Across the four visible training pairs, the value at `(0,0)` is a command rather than part of the object. Removing that cell and cropping the remaining nonzero bounding box gives the output object before transformation:

- command `1`: output is the crop unchanged;
- command `2`: output is the crop rotated 90° clockwise;
- command `3`: output is the crop rotated 180°;
- command `4`: output is the crop rotated 90° counterclockwise.

The third example is an important disambiguator because the command color also occurs in the object; only the single cell `(0,0)` is removed. The second visible query also places object cells in the top row, so the implementation clears the command first and then computes the crop rather than cropping first or removing every cell of the command color.

Implemented one direct solver with rectangular-grid-safe rotation helpers. Alternatives rejected: using command color as a global mask would erase lawful object cells; rotating the full canvas would preserve irrelevant black margins; treating command values as output colors fails all four demonstrations. All four visible examples are accounted for exactly, so I stopped after the first revision.
