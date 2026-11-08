# Solve work log

## Exposure declaration before solving

This is the required exposed post-repair solve. Before preparation I had already
read the assigned generator while repairing it, so earlier rule exposure is
**yes**. After `solve prepare`, I did not reopen the generator, Racket source,
reference solutions, private labels, or earlier solution explanations. The
implementation below was checked only against the visible examples.

## Visible-example hypothesis

The maroon color 9 forms separate rectangular frames. Each frame has one single
nonzero/non-9 cell directly above its top edge; that cell is a numeric ordering
key. Inside each frame is one colored figure.

For each frame:

1. take the smallest bounding box containing the interior figure;
2. preserve zeros inside that tight crop;
3. sort the crops by increasing key value;
4. place them left-to-right with one zero column between neighbors; and
5. vertically center each crop in the tallest crop height, using the upper row
   when an odd one-row difference cannot be split evenly.

Train 1 distinguishes vertical centering from top alignment: the one-row color-6
piece appears on the middle output row. Train 0 and train 2 distinguish key order
from reading order. The output widths equal the sum of tight crop widths plus one
column per gap, ruling out use of full frame interiors.

## Implementation and probes

I locate 4-connected components of color 9, use each component's bounding box to
find its key and interior, tightly crop the nonzero interior cells, sort by key,
and assemble the output. A local visible-example harness first failed on the
untouched `NotImplementedError` template, then compared all four training outputs
exactly after implementation.

Remaining uncertainty concerns malformed inputs outside the visible contract
(e.g. a frame with no key or no figure). Such records are skipped; all supplied
examples have exactly one valid key and figure per frame.
