# Blind solve notes

## Visible pattern

Each training input contains one tight nonzero motif embedded in a zero canvas.
Cropping that motif gives an `h × w` pattern.  The output is `h² × w²`, divided
into an `h × w` grid of `h × w` blocks.  A nonzero outer motif cell selects an
exact copy of the motif; a zero outer cell selects an all-zero block.  This is
`(motif != 0) ⊗ motif`.

The first 3×3 X-shaped example is especially diagnostic: copies occur in the
four corner blocks and center block.  The 4×3 example confirms rectangular
motifs and preserves the same block rule.

## Query generalization

Both queries are 4×4 motifs on 16×16 canvases and use two nonzero colors.  The
training examples do not directly distinguish two multicolor extensions.  I use
the least destructive extension: an occupied outer cell copies the original
multicolor motif unchanged.  Recoloring each copy by the outer cell would erase
visible inner color structure and is not required by any example.

## Implementation

Crop the nonzero bounding box, allocate the self-product dimensions, then stamp
an exact motif at every nonzero motif coordinate.  Empty input is handled as a
1×1 zero motif, though it is outside the visible distribution.
