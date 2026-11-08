# Solve work log

## Prior exposure declaration

Before this solve episode I had already inspected the assigned generator and its
Racket authority while performing the required review. I therefore will finish
with `earlier-exposure=yes`. During this solve phase I did not reopen the
Racket rule, generator implementation, reference solutions, private labels, or
an earlier solve explanation; the observations below came from the public
`challenge.json` only.

## Revision 1 — centroid-addressed panel permutation

The input has four all-zero separator rows and columns, leaving a 3×3 lattice of
5×5 panels. Comparing each visible input panel byte-for-byte with the visible
output panels showed that the output does not recolor or edit panels: it
permutes all nine complete panels.

I treated the more frequent nonzero color as the common panel fill and the other
as the marker. For every source panel in all four examples, I collected the
marker cells in local coordinates and compared their arithmetic centroid with
the panel's observed output address. All 36 moves matched three coordinate
buckets. Visible boundary cases pin the rule: a mean of 1.455 goes to the top
bucket, 1.5 goes to the middle bucket, 2.5 remains middle, and 2.571 goes to the
bottom bucket. Thus each coordinate uses `<1.5`, `1.5..2.5`, and `>2.5`.

The implementation detects the zero lattice, extracts every panel, computes the
marker centroid, and copies the entire panel to the encoded destination. It
checks that the nine destinations form a bijection. A global cyclic-shift idea
was rejected because the observed source-to-destination mappings vary by panel;
source position alone cannot explain them.

Remaining uncertainty is limited to the color-role inference: all visible
examples make the common fill the more frequent nonzero color, including the
dense-marker examples. The structural transform and threshold boundaries are
otherwise directly witnessed by the visible examples.
