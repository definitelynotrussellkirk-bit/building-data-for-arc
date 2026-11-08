# Blind visible-only solve work log

This is a reviewer-authored work log, not a captured model conversation or
log-probability trace. Earlier exposure: none known. During this solve only
`challenge.json` was opened; generator/rule/solutions/private labels stayed closed.

## Revision 1 — translation and four-neighbor boundary
Visible observations: every input has one marker 1, one marker 2, and a larger
single-colored object. Outputs erase the markers and translate the object by
the displacement from marker 1 to marker 2. Output 7 marks object cells missing
at least one of their four orthogonal object neighbors; 8 marks the rest.
Example 0 moves (+1,+6); example 3 moves (-1,-1). The notch in example 2
also creates a 7 directly below the notch, distinguishing object-neighbor
boundary detection from a bounding-box-only border. Examples 1 and 4 show
right-edge clipping rather than wraparound. Determine interior on the original
object before translating and clipping.

Implementation accepts arbitrary non-marker object color; preserves shape and
canvas size, clears markers, translates only object cells, and clips to canvas.
No actual failed revisions or intentional teaching negatives were created.
Stopping criterion: all five visible examples agree with this candidate and
both masked inputs execute; hidden correctness is not checked or claimed.
