# Visible-only solve work log

This is an authored work log, not a captured token-level model trace.
Earlier rule exposure: no. Reference consultation during solving: no.
Read only this episode's README and public challenge; neither task's generator,
rule, canonical labels, audit evidence, or earlier solution notes was opened.

## Revision 1

The three visible examples have a hollow rectangular frame and a separate small
colored thumbnail. The proposed operation crops the frame and enlarges the
thumbnail independently along rows and columns to fill its interior. Zeros
inside the thumbnail's bounding box remain background blocks. Frame location
and the identities of the two foreground colors vary across demonstrations.

Visible dimensions: example 0 input 21 x 24, output 8 x 14; example 1 input
15 x 20, output 6 x 14; example 2 input 18 x 21, output 14 x 14.
Their thumbnail dimensions are 2 x 3, 2 x 3, and 3 x 3; frame interiors are
6 x 12, 4 x 12, and 12 x 12. These yield integer row/column scale factors.

The implementation identifies a frame by its exact perimeter, then uses the
bounding box of the remaining colored cells. It checks divisibility rather
than assuming square scaling. No deliberately wrong revision was created.

The checker will assess the visible examples and whether both query predictions
execute. Query correctness remains unobserved and is reserved for maintainer
scoring. Remaining assumptions: a single frame, one separate thumbnail, and a
modal background color, consistent with all public examples.
